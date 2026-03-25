"""
Load Balancer Test Script
=========================
Tests the resource-aware tenant placement system end-to-end.

Usage:
    python test_load_balancer.py              # run all tests
    python test_load_balancer.py --setup      # only create test tenants
    python test_load_balancer.py --stress     # only run stress test
    python test_load_balancer.py --check      # only check DB state

Prerequisites:
    pip install requests psycopg2-binary
    docker compose up --build   (system must be running on localhost:80)
"""

import argparse
import json
import os
import random
import string
import sys
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = os.getenv("BASE_URL", "http://localhost")
DB_URL = os.getenv("DATABASE_URL",
    "postgresql://bloguser:blogpassword123@localhost:5432/blogdb")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def register_user(tenant_name, mode="create"):
    """Register a new user (and optionally create a new tenant)."""
    username = "user_" + "".join(random.choices(string.ascii_lowercase, k=6))
    payload = {
        "username": username,
        "email": f"{username}@test.com",
        "password": "TestPass123!",
        "tenant_name": tenant_name,
        "mode": mode,
    }
    r = requests.post(f"{BASE_URL}/user_api/register", json=payload, timeout=10)
    r.raise_for_status()
    return r.json()


def login_user(username, password="TestPass123!"):
    """Login and return the JWT token."""
    r = requests.post(f"{BASE_URL}/user_api/login",
                      json={"username": username, "password": password}, timeout=10)
    r.raise_for_status()
    return r.json()["token"]


def create_post(token, title="Test Post", content="x" * 500):
    """Create a blog post."""
    r = requests.post(f"{BASE_URL}/api/posts",
                      json={"title": title, "content": content, "status": "published"},
                      headers={"Authorization": f"Bearer {token}"}, timeout=10)
    r.raise_for_status()
    return r.json()


def get_feed(token):
    """Fetch the post feed."""
    r = requests.get(f"{BASE_URL}/api/posts/feed",
                     headers={"Authorization": f"Bearer {token}"}, timeout=10)
    r.raise_for_status()
    return r.json()


def upload_random_image(token, size_kb=100):
    """Upload a random binary blob as a PNG file."""
    data = random.randbytes(size_kb * 1024)
    # Minimal PNG header so the backend accepts it as an image
    png_header = b'\x89PNG\r\n\x1a\n'
    files = {"file": (f"test_{size_kb}kb.png", png_header + data, "image/png")}
    r = requests.post(f"{BASE_URL}/api/upload", files=files,
                      headers={"Authorization": f"Bearer {token}"}, timeout=30)
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# Setup: create test tenants with different load profiles
# ---------------------------------------------------------------------------

def setup_tenants():
    """Create 4 tenants: 2 light, 1 medium, 1 heavy."""
    tenants = {}

    suffix = "".join(random.choices(string.ascii_lowercase, k=4))
    for base in ["light_a", "light_b", "medium_c", "heavy_d"]:
        name = f"{base}_{suffix}"
        print(f"  Creating tenant '{name}' ...")
        user_data = register_user(name, mode="create")
        token = login_user(user_data["username"])
        tenants[name] = {
            "username": user_data["username"],
            "tenant_id": user_data["tenant_id"],
            "token": token,
        }
        # Create a few posts so the tenant has content
        for i in range(3):
            create_post(token, title=f"{name} post {i}", content=f"Content for {name} #{i}")

    print(f"\n  Created {len(tenants)} tenants:")
    for name, info in tenants.items():
        print(f"    {name}: tenant_id={info['tenant_id']}, user={info['username']}")

    # Save tokens for later use
    with open("test_tenants.json", "w") as f:
        json.dump(tenants, f, indent=2)
    print("  Saved tenant info to test_tenants.json")
    return tenants


# ---------------------------------------------------------------------------
# Stress test: generate asymmetric load to trigger placement changes
# ---------------------------------------------------------------------------

def stress_tenant(token, label, num_requests=50, post_content_size=500,
                  upload_size_kb=0, delay=0.05):
    """Hit the API as a specific tenant to generate metrics."""
    results = {"label": label, "requests": 0, "errors": 0, "served_by": set()}

    for i in range(num_requests):
        try:
            # Alternate between different API calls
            if i % 5 == 0 and upload_size_kb > 0:
                upload_random_image(token, size_kb=upload_size_kb)
            elif i % 3 == 0:
                create_post(token, title=f"Stress {label} #{i}",
                            content="x" * post_content_size)
            else:
                r = requests.get(f"{BASE_URL}/api/posts/feed",
                                 headers={"Authorization": f"Bearer {token}"},
                                 timeout=10)
                served_by = r.headers.get("X-Served-By", "unknown")
                results["served_by"].add(served_by)

            results["requests"] += 1
        except Exception as e:
            results["errors"] += 1
            if results["errors"] <= 3:
                print(f"    [{label}] Error #{results['errors']}: {e}")

        time.sleep(delay)

    results["served_by"] = list(results["served_by"])
    return results


def run_stress_test(tenants):
    """
    Generate asymmetric load:
      - light_a, light_b: few small requests (low CPU, low bandwidth)
      - medium_c: moderate requests with some uploads
      - heavy_d: many requests with large uploads (high CPU + bandwidth)
    """
    profiles = {
        "light_a":  {"num_requests": 20,  "post_content_size": 200,   "upload_size_kb": 0,   "delay": 0.2},
        "light_b":  {"num_requests": 20,  "post_content_size": 200,   "upload_size_kb": 0,   "delay": 0.2},
        "medium_c": {"num_requests": 60,  "post_content_size": 2000,  "upload_size_kb": 50,  "delay": 0.05},
        "heavy_d":  {"num_requests": 100, "post_content_size": 10000, "upload_size_kb": 200, "delay": 0.02},
    }

    print("\n  Starting stress test with asymmetric load profiles...")
    print("  Light tenants: 20 small requests each")
    print("  Medium tenant: 60 requests with 50KB uploads")
    print("  Heavy tenant:  100 requests with 200KB uploads\n")

    futures = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        for name, params in profiles.items():
            if name not in tenants:
                print(f"  Skipping {name} (not found in tenants)")
                continue
            token = tenants[name]["token"]
            futures[pool.submit(stress_tenant, token, name, **params)] = name

        for future in as_completed(futures):
            result = future.result()
            label = result["label"]
            print(f"  [{label}] Done: {result['requests']} requests, "
                  f"{result['errors']} errors, served by: {result['served_by']}")

    print("\n  Stress test complete. Wait ~30s for metrics flush, then ~120s for rebalance.")


# ---------------------------------------------------------------------------
# Check: query the DB to see metrics and placements
# ---------------------------------------------------------------------------

def _docker_psql(query):
    """Run a SQL query via docker exec and return the output."""
    import subprocess
    result = subprocess.run(
        ["docker", "exec", "fyp-postgres-1",
         "psql", "-U", "bloguser", "-d", "blogdb",
         "--tuples-only", "--no-align", "--field-separator", "|",
         "-c", query],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        print(f"  psql error: {result.stderr.strip()}")
        return []
    rows = []
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if line:
            rows.append([c.strip() for c in line.split("|")])
    return rows


def check_db():
    """Query tenant_metrics and tenant_placements via docker exec."""

    print("\n  === tenant_metrics (real-time resource usage) ===")
    rows = _docker_psql("""
        SELECT t.name,
               ROUND(tm.avg_cpu_ms::numeric, 1),
               tm.avg_bytes_out, tm.request_count, tm.updated_at
        FROM tenant_metrics tm
        JOIN tenants t ON t.id = tm.tenant_id
        ORDER BY tm.avg_cpu_ms DESC
    """)
    if rows:
        print(f"  {'Tenant':<12} {'CPU(ms)':<10} {'BW(bytes)':<12} {'Requests':<10} {'Updated'}")
        print(f"  {'------':<12} {'-------':<10} {'---------':<12} {'--------':<10} {'-------'}")
        for r in rows:
            print(f"  {r[0]:<12} {r[1]:<10} {r[2]:<12} {r[3]:<10} {r[4]}")
    else:
        print("  (no metrics yet — make some API requests and wait 30s)")

    print("\n  === tenant_placements (which VM each tenant is on) ===")
    rows = _docker_psql("""
        SELECT t.name, tp.backend_name, tp.backend_host, tp.assigned_at
        FROM tenant_placements tp
        JOIN tenants t ON t.id = tp.tenant_id
        WHERE tp.is_active = true
        ORDER BY tp.backend_name, tp.tenant_id
    """)
    if rows:
        print(f"  {'Tenant':<12} {'Backend':<15} {'Host':<18} {'Assigned'}")
        print(f"  {'------':<12} {'-------':<15} {'----':<18} {'--------'}")
        for r in rows:
            print(f"  {r[0]:<12} {r[1]:<15} {r[2]:<18} {r[3]}")
    else:
        print("  (no placements yet — wait for autoscaler rebalance cycle)")

    print("\n  === tenant_resource_profiles (footprint classification) ===")
    rows = _docker_psql("""
        SELECT t.name, trp.ram_class, trp.footprint_mb, trp.updated_at
        FROM tenant_resource_profiles trp
        JOIN tenants t ON t.id = trp.tenant_id
        ORDER BY trp.footprint_mb DESC
    """)
    if rows:
        print(f"  {'Tenant':<12} {'Class':<10} {'Footprint(MB)':<15} {'Updated'}")
        print(f"  {'------':<12} {'-----':<10} {'-------------':<15} {'-------'}")
        for r in rows:
            print(f"  {r[0]:<12} {r[1]:<10} {r[2]:<15} {r[3]}")
    else:
        print("  (no profiles yet)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Test the resource-aware load balancer")
    parser.add_argument("--setup", action="store_true", help="Create test tenants")
    parser.add_argument("--stress", action="store_true", help="Run stress test")
    parser.add_argument("--check", action="store_true", help="Check DB state")
    args = parser.parse_args()

    # Default: run everything
    run_all = not (args.setup or args.stress or args.check)

    if args.setup or run_all:
        print("\n[1/3] Setting up test tenants...")
        tenants = setup_tenants()
    else:
        tenants = None

    if args.stress or run_all:
        if tenants is None:
            try:
                with open("test_tenants.json") as f:
                    tenants = json.load(f)
                print("\n  Loaded tenants from test_tenants.json")
            except FileNotFoundError:
                print("\n  No test_tenants.json found. Run with --setup first.")
                sys.exit(1)

        # Re-login to get fresh tokens
        print("  Refreshing JWT tokens...")
        for name, info in tenants.items():
            info["token"] = login_user(info["username"])

        print("\n[2/3] Running stress test...")
        run_stress_test(tenants)

    if args.check or run_all:
        if run_all:
            print("\n  Waiting 35s for metrics flush...")
            time.sleep(35)
        print("\n[3/3] Checking database state...")
        check_db()

    if run_all:
        print("\n" + "=" * 60)
        print("  Next steps:")
        print("  1. Wait ~120s for autoscaler rebalance cycle")
        print("  2. Run: python test_load_balancer.py --check")
        print("     to see updated placements")
        print("  3. Run: python test_load_balancer.py --stress --check")
        print("     to generate more load and re-check")
        print("=" * 60)


if __name__ == "__main__":
    main()
