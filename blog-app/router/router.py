import os
import time
import threading
from typing import Optional

from fastapi import FastAPI, Request, Response
from jose import jwt, JWTError
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

app = FastAPI()

SECRET_KEY      = os.getenv("JWT_SECRET_KEY")
DATABASE_URL    = os.getenv("DATABASE_URL")
DEFAULT_BACKEND = os.getenv("DEFAULT_BACKEND", "lightweight-backend:8000")

engine    = create_engine(DATABASE_URL, pool_size=2, max_overflow=2)
DbSession = sessionmaker(bind=engine)

# ---------------------------------------------------------------------------
# In-process placement cache: {tenant_id -> (backend_host, expiry_monotonic)}
# 30s TTL — stale at most 30s after a rebalancing decision; autoscaler also
# calls /invalidate/{tenant_id} immediately after any placement change.
# ---------------------------------------------------------------------------
_cache: dict[int, tuple[str, float]] = {}
_lock = threading.Lock()
TTL = 30.0


def _get(tid: int) -> Optional[str]:
    with _lock:
        e = _cache.get(tid)
        return e[0] if e and time.monotonic() < e[1] else None


def _set(tid: int, host: str) -> None:
    with _lock:
        _cache[tid] = (host, time.monotonic() + TTL)


def lookup(tenant_id: int) -> Optional[str]:
    """Return backend_host for tenant_id from cache or DB, or None if unassigned."""
    if (h := _get(tenant_id)):
        return h
    db = DbSession()
    try:
        row = db.execute(
            text("SELECT backend_host FROM tenant_placements "
                 "WHERE tenant_id = :t AND is_active = true"),
            {"t": tenant_id}
        ).fetchone()
        if row:
            _set(tenant_id, row[0])
            return row[0]
    finally:
        db.close()
    return None


def extract_tenant_id(request: Request) -> Optional[int]:
    """
    Extract tenant_id from JWT Bearer token or ?token= query param.
    Returns None if no valid token is present (caller falls back to default).
    Does NOT raise — auth errors are handled by the backend, not the router.
    """
    auth = request.headers.get("Authorization", "")
    token = auth[7:] if auth.startswith("Bearer ") else request.query_params.get("token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        tid = payload.get("tenant_id")
        return int(tid) if tid is not None else None
    except (JWTError, ValueError, TypeError):
        return None


@app.get("/route")
async def route(request: Request):
    """
    Called by Nginx auth_request for every API request.
    Returns 200 + X-Upstream header containing the backend host:port.
    Nginx uses auth_request_set to capture the header, then proxy_passes to it.

    Security: this endpoint only determines routing — it does NOT authorize the
    request. The FastAPI backend still validates the JWT for every request.
    """
    tid = extract_tenant_id(request)
    host = (lookup(tid) if tid is not None and tid >= 0 else None) or DEFAULT_BACKEND
    return Response(status_code=200, headers={"X-Upstream": host})


@app.post("/invalidate/{tenant_id}")
async def invalidate(tenant_id: int):
    """Called by the autoscaler after a placement change to clear the cache entry."""
    with _lock:
        _cache.pop(tenant_id, None)
    return {"invalidated": tenant_id}


@app.get("/health")
def health():
    return {"status": "ok"}
