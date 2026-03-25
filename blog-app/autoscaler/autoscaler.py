import docker
import os
import time
import threading
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

low_api = docker.APIClient(base_url="unix:///var/run/docker.sock")

# --- Thresholds (scale UP when ALL backends exceed, scale DOWN when ALL are below) ---
CPU_THRESHOLD       = float(os.getenv("CPU_THRESHOLD", "70"))       # % of CPU limit
MEM_THRESHOLD       = float(os.getenv("MEM_THRESHOLD", "80"))       # % of memory limit
BW_THRESHOLD        = float(os.getenv("BW_THRESHOLD", "50"))        # MB/s TX bandwidth
DISK_IO_THRESHOLD   = float(os.getenv("DISK_IO_THRESHOLD", "50"))   # MB/s block I/O write rate

SCALE_DOWN_THRESH   = float(os.getenv("SCALE_DOWN_THRESHOLD", "30"))  # below this on ALL resources = idle
SCALE_DOWN_COOLDOWN = int(os.getenv("SCALE_DOWN_COOLDOWN", "60"))
CHECK_INTERVAL      = int(os.getenv("CHECK_INTERVAL", "10"))
MAX_BURST           = int(os.getenv("MAX_BURST", "3"))
NETWORK_NAME        = os.getenv("NETWORK_NAME", "fyp_blog_net")
UPLOADS_VOLUME      = os.getenv("UPLOADS_VOLUME", "fyp_uploads_data")
BURST_IMAGE         = os.getenv("BURST_IMAGE", "blog-backend:latest")
DATABASE_URL        = os.getenv("DATABASE_URL")
JWT_SECRET_KEY      = os.getenv("JWT_SECRET_KEY")
CORS_ORIGINS        = os.getenv("CORS_ORIGINS", "http://localhost")
ROUTER_URL          = os.getenv("ROUTER_URL", "http://router:8080")
PROFILE_CHECK_INTERVAL = int(os.getenv("PROFILE_CHECK_INTERVAL", "120"))
TENANT_CPU_HEAVY      = float(os.getenv("TENANT_CPU_HEAVY", "80"))
SEPARATION_INTERVAL   = int(os.getenv("SEPARATION_INTERVAL", "30"))

burst_containers = []  # list of container IDs spawned by the autoscaler
burst_count      = 0
all_idle_since   = None  # timestamp when all backends first dropped below threshold

# Discover any pre-existing burst containers from a previous run so we can
# manage them (scale-down) even after an autoscaler restart.
try:
    _existing = low_api.containers(filters={"name": "burst-backend"})
    for _c in _existing:
        burst_containers.append(_c["Id"])
        # Extract the burst number from the name to keep burst_count in sync
        _name = _c["Names"][0].lstrip("/") if _c.get("Names") else ""
        try:
            _num = int(_name.rsplit("-", 1)[-1])
            burst_count = max(burst_count, _num)
        except (ValueError, IndexError):
            pass
    if burst_containers:
        print(f"[AUTOSCALER] Discovered {len(burst_containers)} existing burst container(s) "
              f"from previous run (burst_count={burst_count})")
except Exception as _e:
    print(f"[AUTOSCALER] Could not discover existing burst containers: {_e}")

# Previous network stats for bandwidth rate calculation
_prev_net_stats: dict = {}  # {container_id: (tx_bytes, timestamp)}
_prev_disk_stats: dict = {}  # {container_id: (write_bytes, timestamp)}

# SQLAlchemy engine for placement operations
as_engine = create_engine(DATABASE_URL, pool_size=2, max_overflow=2)
AsSession = sessionmaker(bind=as_engine)


def get_backend_container_ids():
    """Return short IDs of every container with the 'backend' alias on NETWORK_NAME."""
    net_info = low_api.inspect_network(NETWORK_NAME)
    ids = []
    for cid in net_info.get("Containers", {}):
        try:
            ctr_info = low_api.inspect_container(cid)
            net_settings = ctr_info["NetworkSettings"]["Networks"].get(NETWORK_NAME, {})
            aliases = net_settings.get("Aliases") or []
            if "backend" in aliases:
                ids.append(cid[:12])
        except Exception:
            pass
    return ids


def get_container_stats(container_id):
    """
    Return a dict of resource usage for a container:
      cpu_pct   – CPU % relative to the container's CPU limit
      mem_pct   – Memory % relative to the container's memory limit
      bw_mbps   – Network TX bandwidth in MB/s (rate since last check)
      disk_mbps – Block I/O write rate in MB/s (rate since last check)
    """
    result = {"cpu_pct": 0.0, "mem_pct": 0.0, "bw_mbps": 0.0, "disk_mbps": 0.0}
    try:
        stats = low_api.stats(container_id, stream=False)
        ctr_info = low_api.inspect_container(container_id)
        now = time.time()

        # --- CPU ---
        cpu_delta = (
            stats["cpu_stats"]["cpu_usage"]["total_usage"]
            - stats["precpu_stats"]["cpu_usage"]["total_usage"]
        )
        sys_delta = (
            stats["cpu_stats"]["system_cpu_usage"]
            - stats["precpu_stats"]["system_cpu_usage"]
        )
        num_cpus = stats["cpu_stats"].get("online_cpus", 1)
        if sys_delta > 0:
            nano_cpus = ctr_info["HostConfig"].get("NanoCpus", 0)
            cpu_limit = nano_cpus / 1e9 if nano_cpus > 0 else num_cpus
            result["cpu_pct"] = (cpu_delta / sys_delta) * (num_cpus / cpu_limit) * 100.0

        # --- Memory ---
        mem_usage = stats.get("memory_stats", {}).get("usage", 0)
        mem_limit = stats.get("memory_stats", {}).get("limit", 0)
        # Subtract cache from usage for a more accurate "active memory" figure
        mem_cache = stats.get("memory_stats", {}).get("stats", {}).get("cache", 0)
        active_mem = mem_usage - mem_cache
        if mem_limit > 0:
            result["mem_pct"] = (active_mem / mem_limit) * 100.0

        # --- Network bandwidth (TX rate in MB/s) ---
        networks = stats.get("networks", {})
        tx_bytes = sum(iface.get("tx_bytes", 0) for iface in networks.values())
        prev = _prev_net_stats.get(container_id)
        if prev is not None:
            prev_tx, prev_time = prev
            dt = now - prev_time
            if dt > 0:
                result["bw_mbps"] = (tx_bytes - prev_tx) / (dt * 1024 * 1024)
        _prev_net_stats[container_id] = (tx_bytes, now)

        # --- Disk I/O (write rate in MB/s) ---
        io_service = stats.get("blkio_stats", {}).get("io_service_bytes_recursive") or []
        write_bytes = sum(e.get("value", 0) for e in io_service
                          if e.get("op", "").lower() == "write")
        prev_disk = _prev_disk_stats.get(container_id)
        if prev_disk is not None:
            prev_wb, prev_time = prev_disk
            dt = now - prev_time
            if dt > 0:
                result["disk_mbps"] = (write_bytes - prev_wb) / (dt * 1024 * 1024)
        _prev_disk_stats[container_id] = (write_bytes, now)

    except Exception as e:
        print(f"[AUTOSCALER] Stats error for {container_id}: {e}")
    return result


def spawn_burst():
    """Start a new lightweight burst backend container on NETWORK_NAME with alias 'backend'."""
    global burst_count
    burst_count += 1
    name = f"burst-backend-{burst_count}"
    print(f"[AUTOSCALER] Scaling up — spawning {name} ...")
    try:
        net_cfg = low_api.create_networking_config({
            NETWORK_NAME: low_api.create_endpoint_config(aliases=["backend"])
        })
        host_cfg = low_api.create_host_config(
            binds=[f"{UPLOADS_VOLUME}:/app/uploads:rw"]
        )
        ctr = low_api.create_container(
            image=BURST_IMAGE,
            name=name,
            environment=[
                f"DATABASE_URL={DATABASE_URL}",
                f"JWT_SECRET_KEY={JWT_SECRET_KEY}",
                f"CORS_ORIGINS={CORS_ORIGINS}",
                f"INSTANCE_ID={name}",
                "UVICORN_WORKERS=1",
            ],
            host_config=host_cfg,
            networking_config=net_cfg,
        )
        low_api.start(ctr["Id"])
        burst_containers.append(ctr["Id"])
        print(f"[AUTOSCALER] {name} started (id={ctr['Id'][:12]}) — "
              f"Nginx will pick it up within 5 s via DNS")
    except Exception as e:
        print(f"[AUTOSCALER] Failed to spawn {name}: {e}")
        burst_count -= 1


def remove_burst():
    """Stop and remove the most recently spawned burst container."""
    if not burst_containers:
        return
    cid = burst_containers.pop()
    print(f"[AUTOSCALER] Scaling down — removing container {cid[:12]} ...")
    try:
        low_api.stop(cid, timeout=10)
        low_api.remove_container(cid)
        print(f"[AUTOSCALER] Container {cid[:12]} stopped and removed")
    except Exception as e:
        print(f"[AUTOSCALER] Remove error for {cid[:12]}: {e}")


# ---------------------------------------------------------------------------
# Resource-aware placement (anti noisy-neighbour)
# ---------------------------------------------------------------------------

def get_backend_ram_limits() -> dict:
    """
    Return {container_name: ram_limit_mb} for all active backend containers
    on the Docker network. Uses the same low_api already available.
    """
    result = {}
    try:
        net_info = low_api.inspect_network(NETWORK_NAME)
        for cid in net_info.get("Containers", {}):
            try:
                info = low_api.inspect_container(cid)
                name = info["Name"].lstrip("/")
                aliases = (info["NetworkSettings"]["Networks"]
                           .get(NETWORK_NAME, {}).get("Aliases") or [])
                if "backend" not in aliases:
                    continue
                mem_bytes = info["HostConfig"].get("Memory", 0)
                # Memory=0 means no limit — treat as 512MB conservative cap
                ram_mb = (mem_bytes // (1024 * 1024)) if mem_bytes > 0 else 512
                result[name] = ram_mb
            except Exception:
                pass
    except Exception as e:
        print(f"[PLACER] get_backend_ram_limits error: {e}")
    return result


def assign_tenant(tenant_id: int, backend_limits: dict):
    """
    Classify tenant resource usage from real-time metrics (tenant_metrics table),
    then run Best-Fit bin-packing to assign the tenant to a backend.

    Metrics:
      - avg_cpu_ms:    EMA of request processing time — proxy for CPU load
      - avg_bytes_out: EMA of response bytes per request — proxy for bandwidth/memory

    Falls back to static file-size estimate when no traffic data exists yet.
    """
    db = AsSession()
    try:
        # Prefer real runtime metrics; fall back to static proxy if no data yet
        row = db.execute(text("""
            SELECT avg_cpu_ms, avg_bytes_out, request_count
            FROM tenant_metrics
            WHERE tenant_id = :t
        """), {"t": tenant_id}).fetchone()

        if row and int(row[2]) > 0:
            avg_cpu_ms    = float(row[0])
            avg_bytes_out = int(row[1])

            # CPU class: < 100ms light, 100–500ms medium, > 500ms heavy
            if avg_cpu_ms < 100:
                cpu_class = 0
            elif avg_cpu_ms < 500:
                cpu_class = 1
            else:
                cpu_class = 2

            # Bandwidth class: < 50KB light, 50KB–500KB medium, > 500KB heavy
            if avg_bytes_out < 50_000:
                bw_class = 0
            elif avg_bytes_out < 500_000:
                bw_class = 1
            else:
                bw_class = 2

            # Composite = worst-case of either dimension
            composite = max(cpu_class, bw_class)
            print(f"[PLACER] tenant={tenant_id} metrics: "
                  f"cpu={avg_cpu_ms:.1f}ms bw={avg_bytes_out}B → composite={composite}")
        else:
            # No traffic data yet — fall back to static storage estimate
            storage = db.execute(text(
                "SELECT COALESCE(SUM(file_size), 0) FROM uploads WHERE tenant_id = :t"),
                {"t": tenant_id}).scalar()
            posts = db.execute(text(
                "SELECT COUNT(*) FROM blog_posts WHERE tenant_id = :t"),
                {"t": tenant_id}).scalar()
            est_mb = (storage // (1024 * 1024)) + (posts * 1)
            composite = 0 if est_mb < 50 else (1 if est_mb < 500 else 2)
            print(f"[PLACER] tenant={tenant_id} no metrics yet, static est={est_mb}MB → composite={composite}")

        if composite == 0:
            ram_class, footprint = "small", 64
        elif composite == 1:
            ram_class, footprint = "medium", 128
        else:
            ram_class, footprint = "large", 256

        # Upsert resource profile
        db.execute(text("""
            INSERT INTO tenant_resource_profiles (tenant_id, ram_class, footprint_mb, updated_at)
            VALUES (:t, :c, :m, NOW())
            ON CONFLICT (tenant_id) DO UPDATE
            SET ram_class    = EXCLUDED.ram_class,
                footprint_mb = EXCLUDED.footprint_mb,
                updated_at   = NOW()
        """), {"t": tenant_id, "c": ram_class, "m": footprint})
        db.commit()

        # Compute used capacity per backend (excluding this tenant's own row)
        rows = db.execute(text("""
            SELECT tp.backend_name, COALESCE(SUM(trp.footprint_mb), 0)
            FROM tenant_placements tp
            LEFT JOIN tenant_resource_profiles trp ON tp.tenant_id = trp.tenant_id
            WHERE tp.is_active = true AND tp.tenant_id != :t
            GROUP BY tp.backend_name
        """), {"t": tenant_id}).fetchall()
        used = {r[0]: int(r[1]) for r in rows}

        # Best-Fit: pick the backend with the smallest remaining capacity that
        # still fits the tenant. This spreads heavy tenants across backends
        # (anti noisy-neighbour) rather than packing them together.
        candidates = [
            (lim - used.get(name, 0), name)
            for name, lim in backend_limits.items()
            if lim - used.get(name, 0) >= footprint
        ]

        if candidates:
            # Sort ascending by remaining capacity — tightest fit that still works
            candidates.sort()
            chosen = candidates[0][1]
        else:
            # No backend fits perfectly; fall back to the one with most capacity
            chosen = max(backend_limits, key=backend_limits.get)

        backend_host = f"{chosen}:8000"

        db.execute(text("""
            INSERT INTO tenant_placements
                (tenant_id, backend_name, backend_host, is_active, assigned_at)
            VALUES (:t, :n, :h, true, NOW())
            ON CONFLICT (tenant_id) DO UPDATE
            SET backend_name = EXCLUDED.backend_name,
                backend_host = EXCLUDED.backend_host,
                is_active    = true,
                assigned_at  = NOW()
        """), {"t": tenant_id, "n": chosen, "h": backend_host})
        db.commit()

    finally:
        db.close()

    # Invalidate router cache so new placement takes effect within one request
    try:
        requests.post(f"{ROUTER_URL}/invalidate/{tenant_id}", timeout=2)
    except Exception:
        pass

    print(f"[PLACER] tenant={tenant_id} → {backend_host} "
          f"(class={ram_class}, footprint={footprint}MB)")


def migrate_to_burst(burst_name: str, overloaded_backend: str):
    """
    Immediately migrate the heaviest tenants from overloaded_backend to the
    newly spawned burst container. Called in a short-delay thread after
    spawn_burst() so the burst container receives real traffic right away
    rather than sitting idle waiting for the 120s rebalance cycle.
    """
    burst_host = f"{burst_name}:8000"
    db = AsSession()
    try:
        rows = db.execute(text("""
            SELECT tp.tenant_id, COALESCE(trp.footprint_mb, 64) AS mb
            FROM tenant_placements tp
            LEFT JOIN tenant_resource_profiles trp ON tp.tenant_id = trp.tenant_id
            WHERE tp.backend_name = :name AND tp.is_active = true
            ORDER BY mb DESC
        """), {"name": overloaded_backend}).fetchall()

        if not rows:
            print(f"[PLACER] No tenants on {overloaded_backend} to migrate to {burst_name}")
            return

        # Move the top half (heaviest) to the burst container so load is split
        n_migrate = max(1, len(rows) // 2)
        to_migrate = rows[:n_migrate]

        for tenant_id, mb in to_migrate:
            db.execute(text("""
                UPDATE tenant_placements
                SET backend_name = :n, backend_host = :h, assigned_at = NOW()
                WHERE tenant_id = :t
            """), {"n": burst_name, "h": burst_host, "t": tenant_id})
            try:
                requests.post(f"{ROUTER_URL}/invalidate/{tenant_id}", timeout=2)
            except Exception:
                pass
            print(f"[PLACER] Migrated tenant={tenant_id} ({mb}MB) → {burst_host}")

        db.commit()
        print(f"[PLACER] Migrated {n_migrate}/{len(rows)} tenants from "
              f"{overloaded_backend} → {burst_name}")
    except Exception as e:
        print(f"[PLACER] migrate_to_burst error: {e}")
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        db.close()


def migrate_from_burst(burst_name: str):
    """
    Before removing a burst container, re-home its tenants to the remaining
    backends using bin-packing so no requests are lost after removal.
    """
    db = AsSession()
    try:
        rows = db.execute(text("""
            SELECT tp.tenant_id, COALESCE(trp.footprint_mb, 64) AS mb
            FROM tenant_placements tp
            LEFT JOIN tenant_resource_profiles trp ON tp.tenant_id = trp.tenant_id
            WHERE tp.backend_name = :name AND tp.is_active = true
            ORDER BY mb DESC
        """), {"name": burst_name}).fetchall()

        if not rows:
            return

        backend_limits = {k: v for k, v in get_backend_ram_limits().items()
                          if k != burst_name}
        if not backend_limits:
            print("[PLACER] No remaining backends to migrate burst tenants to")
            return

        for tenant_id, footprint in rows:
            used_rows = db.execute(text("""
                SELECT tp.backend_name, COALESCE(SUM(trp.footprint_mb), 0)
                FROM tenant_placements tp
                LEFT JOIN tenant_resource_profiles trp ON tp.tenant_id = trp.tenant_id
                WHERE tp.is_active = true
                  AND tp.tenant_id != :t
                  AND tp.backend_name != :burst
                GROUP BY tp.backend_name
            """), {"t": tenant_id, "burst": burst_name}).fetchall()
            used = {r[0]: int(r[1]) for r in used_rows}

            candidates = [
                (lim - used.get(name, 0), name)
                for name, lim in backend_limits.items()
                if lim - used.get(name, 0) >= footprint
            ]
            if not candidates:
                # No backend perfectly fits; pick the one with most capacity
                candidates = [(0, max(backend_limits, key=backend_limits.get))]
            candidates.sort()
            chosen = candidates[0][1]
            host = f"{chosen}:8000"

            db.execute(text("""
                UPDATE tenant_placements
                SET backend_name = :n, backend_host = :h, assigned_at = NOW()
                WHERE tenant_id = :t
            """), {"n": chosen, "h": host, "t": tenant_id})
            try:
                requests.post(f"{ROUTER_URL}/invalidate/{tenant_id}", timeout=2)
            except Exception:
                pass
            print(f"[PLACER] Re-homed tenant={tenant_id} ({footprint}MB) → {host}")

        db.commit()
        print(f"[PLACER] All {len(rows)} tenants migrated away from {burst_name}")
    except Exception as e:
        print(f"[PLACER] migrate_from_burst error: {e}")
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        db.close()


def rebalance_loop():
    """
    Daemon thread: every PROFILE_CHECK_INTERVAL seconds, re-profile all tenants
    and update their backend assignments using bin-packing. Runs independently
    of the CPU autoscaler loop so neither blocks the other.
    """
    time.sleep(30)  # wait for backends to start before first run
    while True:
        try:
            backend_limits = get_backend_ram_limits()
            if not backend_limits:
                print("[PLACER] No backends found, skipping rebalance")
                time.sleep(PROFILE_CHECK_INTERVAL)
                continue

            db = AsSession()
            try:
                tenant_ids = [
                    r[0] for r in db.execute(text("SELECT id FROM tenants")).fetchall()
                ]
            finally:
                db.close()

            if tenant_ids:
                print(f"[PLACER] Rebalancing {len(tenant_ids)} tenant(s) across "
                      f"{list(backend_limits.keys())}")
                for tid in tenant_ids:
                    assign_tenant(tid, backend_limits)
            else:
                print("[PLACER] No tenants to place yet")

        except Exception as e:
            print(f"[PLACER] Rebalance error: {e}")

        time.sleep(PROFILE_CHECK_INTERVAL)


def separate_hot_tenants():
    """
    Active hot-tenant separation loop (runs every SEPARATION_INTERVAL seconds).

    Queries tenant_metrics to find tenants whose avg_cpu_ms or avg_bytes_out
    exceeds the "heavy" threshold. If two or more heavy tenants are co-located
    on the same backend:
      1. Try to move the heaviest one to another backend with capacity.
      2. If no backend has capacity, spawn a burst container and migrate to it.

    This makes the load balancer *actively* detect and separate noisy neighbours
    rather than waiting for the passive rebalance cycle.
    """
    time.sleep(45)  # let the first rebalance run first
    while True:
        try:
            db = AsSession()
            try:
                # Find all "hot" tenants: high CPU time OR high bandwidth
                # A tenant is "hot" if its avg request time or response size
                # exceeds the heavy thresholds, indicating noisy-neighbour risk.
                hot_rows = db.execute(text("""
                    SELECT tm.tenant_id, tp.backend_name,
                           tm.avg_cpu_ms, tm.avg_bytes_out, tm.request_count,
                           COALESCE(trp.footprint_mb, 64) AS footprint
                    FROM tenant_metrics tm
                    JOIN tenant_placements tp ON tm.tenant_id = tp.tenant_id
                        AND tp.is_active = true
                    LEFT JOIN tenant_resource_profiles trp ON tm.tenant_id = trp.tenant_id
                    WHERE tm.request_count > 0
                      AND tm.updated_at > NOW() - INTERVAL '5 minutes'
                      AND (tm.avg_cpu_ms > :cpu_thresh OR tm.avg_bytes_out > :bw_thresh)
                    ORDER BY tp.backend_name, tm.avg_cpu_ms DESC
                """), {"cpu_thresh": TENANT_CPU_HEAVY, "bw_thresh": 50_000}).fetchall()
            finally:
                db.close()

            if not hot_rows:
                time.sleep(SEPARATION_INTERVAL)
                continue

            # Group hot tenants by backend
            backend_hot = {}
            for row in hot_rows:
                tid, backend, cpu_ms, bw, reqs, footprint = row
                backend_hot.setdefault(backend, []).append(
                    {"tid": tid, "backend": backend, "cpu_ms": float(cpu_ms),
                     "bw": int(bw), "footprint": int(footprint)})

            # Find backends with 2+ hot tenants (noisy-neighbour conflict)
            conflicts = {b: tenants for b, tenants in backend_hot.items()
                         if len(tenants) >= 2}

            if not conflicts:
                time.sleep(SEPARATION_INTERVAL)
                continue

            backend_limits = get_backend_ram_limits()
            if not backend_limits:
                time.sleep(SEPARATION_INTERVAL)
                continue

            for backend, hot_tenants in conflicts.items():
                # Sort by CPU descending — move the heaviest tenant
                hot_tenants.sort(key=lambda t: t["cpu_ms"], reverse=True)
                to_move = hot_tenants[0]
                tid = to_move["tid"]
                footprint = to_move["footprint"]

                print(f"[SEPARATOR] Conflict on {backend}: {len(hot_tenants)} hot tenants "
                      f"(moving tenant={tid}, cpu={to_move['cpu_ms']:.1f}ms)")

                # Find another backend with capacity
                db = AsSession()
                try:
                    used_rows = db.execute(text("""
                        SELECT tp.backend_name, COALESCE(SUM(trp.footprint_mb), 0)
                        FROM tenant_placements tp
                        LEFT JOIN tenant_resource_profiles trp ON tp.tenant_id = trp.tenant_id
                        WHERE tp.is_active = true AND tp.tenant_id != :t
                        GROUP BY tp.backend_name
                    """), {"t": tid}).fetchall()
                    used = {r[0]: int(r[1]) for r in used_rows}

                    # Exclude the current backend — we want a DIFFERENT one
                    candidates = [
                        (lim - used.get(name, 0), name)
                        for name, lim in backend_limits.items()
                        if name != backend and lim - used.get(name, 0) >= footprint
                    ]

                    if candidates:
                        # Move to the backend with most remaining capacity (spread load)
                        candidates.sort(reverse=True)
                        chosen = candidates[0][1]
                        host = f"{chosen}:8000"

                        db.execute(text("""
                            UPDATE tenant_placements
                            SET backend_name = :n, backend_host = :h, assigned_at = NOW()
                            WHERE tenant_id = :t
                        """), {"n": chosen, "h": host, "t": tid})
                        db.commit()
                        try:
                            requests.post(f"{ROUTER_URL}/invalidate/{tid}", timeout=2)
                        except Exception:
                            pass
                        print(f"[SEPARATOR] Moved tenant={tid} ({footprint}MB) "
                              f"from {backend} → {chosen}")
                    else:
                        # No existing backend has capacity — only spawn a burst
                        # if backends are actually under load right now (prevents
                        # stale metrics from fighting the scale-down loop)
                        backend_ids = get_backend_container_ids()
                        live_stats = {c: get_container_stats(c) for c in backend_ids}
                        any_loaded = any(
                            s["cpu_pct"] > SCALE_DOWN_THRESH
                            or s["mem_pct"] > SCALE_DOWN_THRESH
                            for s in live_stats.values()
                        )
                        if any_loaded and len(burst_containers) < MAX_BURST:
                            print(f"[SEPARATOR] No capacity on other backends — "
                                  f"spawning burst for tenant={tid}")
                            db.close()
                            db = None
                            spawn_burst()
                            if burst_containers:
                                bname = f"burst-backend-{burst_count}"
                                # Wait for burst to start, then migrate
                                threading.Thread(
                                    target=lambda bn=bname, src=backend: (
                                        time.sleep(5),
                                        _move_single_tenant(tid, bn)
                                    ),
                                    daemon=True
                                ).start()
                        elif not any_loaded:
                            print(f"[SEPARATOR] Backends idle — skipping burst spawn "
                                  f"for tenant={tid}")
                        else:
                            print(f"[SEPARATOR] No capacity and MAX_BURST reached — "
                                  f"tenant={tid} stays on {backend}")
                finally:
                    if db is not None:
                        db.close()

        except Exception as e:
            print(f"[SEPARATOR] Error: {e}")

        time.sleep(SEPARATION_INTERVAL)


def _move_single_tenant(tenant_id: int, burst_name: str):
    """Move a single tenant to a burst container."""
    burst_host = f"{burst_name}:8000"
    db = AsSession()
    try:
        db.execute(text("""
            UPDATE tenant_placements
            SET backend_name = :n, backend_host = :h, assigned_at = NOW()
            WHERE tenant_id = :t
        """), {"n": burst_name, "h": burst_host, "t": tenant_id})
        db.commit()
        try:
            requests.post(f"{ROUTER_URL}/invalidate/{tenant_id}", timeout=2)
        except Exception:
            pass
        print(f"[SEPARATOR] Moved tenant={tenant_id} → {burst_host}")
    except Exception as e:
        print(f"[SEPARATOR] Move error: {e}")
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        db.close()


# Start placement daemons before the CPU monitoring loop
threading.Thread(target=rebalance_loop, daemon=True).start()
threading.Thread(target=separate_hot_tenants, daemon=True).start()

print(f"[AUTOSCALER] Started — check_interval={CHECK_INTERVAL}s, max_burst={MAX_BURST}")
print(f"[AUTOSCALER] Scale-up thresholds (ANY triggers):  "
      f"CPU>{CPU_THRESHOLD}%  MEM>{MEM_THRESHOLD}%  BW>{BW_THRESHOLD}MB/s  DISK>{DISK_IO_THRESHOLD}MB/s")
print(f"[AUTOSCALER] Scale-down threshold (ALL below):    {SCALE_DOWN_THRESH}% for {SCALE_DOWN_COOLDOWN}s")
print(f"[PLACER] Placement daemon started — rebalance every {PROFILE_CHECK_INTERVAL}s, "
      f"router={ROUTER_URL}")
print(f"[SEPARATOR] Hot-tenant separation active — checking every {SEPARATION_INTERVAL}s, "
      f"CPU threshold={TENANT_CPU_HEAVY}ms")

while True:
    ids = get_backend_container_ids()

    if not ids:
        print("[AUTOSCALER] No backend containers found on network yet, retrying...")
        time.sleep(CHECK_INTERVAL)
        continue

    # Collect all resource metrics for every backend container
    all_stats = {cid: get_container_stats(cid) for cid in ids}

    for cid, s in all_stats.items():
        print(f"[AUTOSCALER]   {cid}: CPU={s['cpu_pct']:.1f}%  "
              f"MEM={s['mem_pct']:.1f}%  BW={s['bw_mbps']:.2f}MB/s  "
              f"DISK={s['disk_mbps']:.2f}MB/s")

    # Scale UP: if ANY single resource is over threshold on ALL backends
    cpu_full  = all(s["cpu_pct"]  > CPU_THRESHOLD     for s in all_stats.values())
    mem_full  = all(s["mem_pct"]  > MEM_THRESHOLD     for s in all_stats.values())
    bw_full   = all(s["bw_mbps"]  > BW_THRESHOLD      for s in all_stats.values())
    disk_full = all(s["disk_mbps"] > DISK_IO_THRESHOLD for s in all_stats.values())

    any_resource_full = cpu_full or mem_full or bw_full or disk_full

    # Scale DOWN: ALL resources below the idle threshold on ALL backends
    all_idle = all(
        s["cpu_pct"] < SCALE_DOWN_THRESH
        and s["mem_pct"] < SCALE_DOWN_THRESH
        and s["bw_mbps"] < (BW_THRESHOLD * SCALE_DOWN_THRESH / 100)
        and s["disk_mbps"] < (DISK_IO_THRESHOLD * SCALE_DOWN_THRESH / 100)
        for s in all_stats.values()
    )

    if any_resource_full:
        # Log which resource(s) triggered the scale-up
        triggers = []
        if cpu_full:  triggers.append(f"CPU>{CPU_THRESHOLD}%")
        if mem_full:  triggers.append(f"MEM>{MEM_THRESHOLD}%")
        if bw_full:   triggers.append(f"BW>{BW_THRESHOLD}MB/s")
        if disk_full: triggers.append(f"DISK>{DISK_IO_THRESHOLD}MB/s")
        print(f"[AUTOSCALER] Scale-up triggered by: {', '.join(triggers)}")

        all_idle_since = None
        if len(burst_containers) < MAX_BURST:
            # Identify the most-loaded backend (by CPU as primary tiebreaker)
            most_loaded_cid = max(all_stats, key=lambda c: all_stats[c]["cpu_pct"])
            try:
                most_loaded_name = low_api.inspect_container(
                    most_loaded_cid)["Name"].lstrip("/")
            except Exception:
                most_loaded_name = "vm1"

            spawn_burst()

            # After 5s (container startup time), migrate heavy tenants to it
            if burst_containers:
                _burst_name = f"burst-backend-{burst_count}"
                _src = most_loaded_name
                threading.Thread(
                    target=lambda bn=_burst_name, src=_src: (
                        time.sleep(5),
                        migrate_to_burst(bn, src)
                    ),
                    daemon=True
                ).start()
        else:
            print(f"[AUTOSCALER] All backends full but MAX_BURST={MAX_BURST} already reached")

    elif all_idle and burst_containers:
        now = time.time()
        if all_idle_since is None:
            all_idle_since = now
            remaining = SCALE_DOWN_COOLDOWN
            print(f"[AUTOSCALER] All backends idle — will scale down in {remaining}s if load stays low")
        elif now - all_idle_since >= SCALE_DOWN_COOLDOWN:
            # Re-home the burst's tenants before removing the container
            burst_cid = burst_containers[-1]
            try:
                burst_name = low_api.inspect_container(burst_cid)["Name"].lstrip("/")
                migrate_from_burst(burst_name)
            except Exception as e:
                print(f"[PLACER] Could not get burst name for pre-removal migration: {e}")
            remove_burst()
            all_idle_since = None  # reset: wait another full cooldown before next removal

    else:
        if all_idle_since is not None:
            print("[AUTOSCALER] Load increased again, cancelling scale-down")
        all_idle_since = None

    time.sleep(CHECK_INTERVAL)
