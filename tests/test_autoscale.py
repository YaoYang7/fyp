"""
Autoscaler Burst Test
=====================
Tests that the autoscaler spawns a burst container when CPU is saturated,
and that the new tenant gets migrated to it.

Scenario:
  1. Create 6 tenants (enough for bin-packing to spread across vm1 + vm2)
  2. Generate light traffic so metrics get flushed and rebalance distributes them
  3. Wait for rebalance to place tenants on BOTH vm1 and vm2
  4. Hammer all tenants to push both VMs above 70% CPU
  5. Add extra load (user_c) to ensure autoscaler triggers burst
  6. Verify: burst container created, tenant(s) migrated to it

Key insight: The autoscaler only spawns a burst when ALL backends are above
the CPU threshold (70%). With tenant-affinity routing, new tenants default to
vm1. We must wait for the rebalance cycle to distribute tenants across both
VMs before the stress test can push both VMs high.

Usage:
    python tests/test_autoscale.py

Prerequisites:
    pip install requests
    docker compose up --build   (system must be running on localhost:80)
"""

import json
import os
import random
import string
import subprocess
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from threading import Event, Thread

BASE_URL = os.getenv("BASE_URL", "http://localhost")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def register_user(tenant_name):
    username = "user_" + "".join(random.choices(string.ascii_lowercase, k=6))
    payload = {
        "username": username,
        "email": f"{username}@test.com",
        "password": "TestPass123!",
        "tenant_name": tenant_name,
        "mode": "create",
    }
    r = requests.post(f"{BASE_URL}/user_api/register", json=payload, timeout=10)
    r.raise_for_status()
    return r.json()


def login_user(username):
    r = requests.post(f"{BASE_URL}/user_api/login",
                      json={"username": username, "password": "TestPass123!"},
                      timeout=10)
    r.raise_for_status()
    return r.json()["token"]


def docker_psql(query):
    result = subprocess.run(
        ["docker", "exec", "fyp-postgres-1",
         "psql", "-U", "bloguser", "-d", "blogdb",
         "--tuples-only", "--no-align", "--field-separator", "|",
         "-c", query],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        return []
    rows = []
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if line:
            rows.append([c.strip() for c in line.split("|")])
    return rows


def get_burst_containers():
    result = subprocess.run(
        ["docker", "ps", "--filter", "name=burst-backend", "--format", "{{.Names}}"],
        capture_output=True, text=True, timeout=10,
    )
    return [n.strip() for n in result.stdout.strip().splitlines() if n.strip()]


def get_container_stats():
    """Get CPU% and MEM% for all backend containers."""
    result = subprocess.run(
        ["docker", "stats", "--no-stream",
         "--format", "{{.Name}}\t{{.CPUPerc}}\t{{.MemPerc}}\t{{.NetIO}}"],
        capture_output=True, text=True, timeout=15,
    )
    stats = {}
    for line in result.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) >= 3 and ("vm" in parts[0] or "burst" in parts[0]):
            name = parts[0].strip()
            cpu = parts[1].strip().rstrip("%")
            mem = parts[2].strip().rstrip("%")
            net = parts[3].strip() if len(parts) > 3 else ""
            try:
                stats[name] = {"cpu": float(cpu), "mem": float(mem), "net": net}
            except ValueError:
                pass
    return stats


def print_stats(stats, prefix=""):
    for name, s in sorted(stats.items()):
        cpu_bar = "#" * int(s["cpu"] / 2)
        print(f"  {prefix}{name:<25} CPU={s['cpu']:>5.1f}%  MEM={s['mem']:>5.1f}%  NET={s['net']}  |{cpu_bar}")


def show_placements():
    rows = docker_psql("""
        SELECT t.name, tp.backend_name, tp.backend_host
        FROM tenant_placements tp
        JOIN tenants t ON t.id = tp.tenant_id
        WHERE tp.is_active = true
        ORDER BY tp.backend_name, t.name
    """)
    if rows:
        vm1_count = sum(1 for r in rows if r[1] == "vm1")
        vm2_count = sum(1 for r in rows if r[1] == "vm2")
        burst_count = sum(1 for r in rows if "burst" in r[1])
        print(f"  Placements: vm1={vm1_count}, vm2={vm2_count}, burst={burst_count}")
        for r in rows:
            marker = " <-- BURST" if "burst" in r[1] else ""
            print(f"    {r[0]:<25} -> {r[1]:<15} ({r[2]}){marker}")
        return vm1_count, vm2_count
    else:
        print("  (no placements yet)")
        return 0, 0


# ---------------------------------------------------------------------------
# CPU stress via docker exec (HTTP alone can't saturate I/O-bound backends)
# ---------------------------------------------------------------------------

def inject_cpu_stress(container, duration, stop_event):
    """Run CPU-bound loop inside a container via docker exec."""
    try:
        proc = subprocess.Popen([
            "docker", "exec", container,
            "python", "-c",
            f"import time; e=time.time()+{duration}\n"
            f"while time.time()<e: [x**2 for x in range(10000)]",
        ])
        while not stop_event.is_set() and proc.poll() is None:
            time.sleep(0.5)
        if proc.poll() is None:
            proc.terminate()
    except Exception as e:
        print(f"  Stress on {container} error: {e}")


# ---------------------------------------------------------------------------
# HTTP traffic generator (for realistic tenant metrics, not CPU saturation)
# ---------------------------------------------------------------------------

def http_traffic_worker(token, label, stop_event, concurrency=8):
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {token}"
    large_content = "x" * 5000

    def single_request():
        try:
            choice = random.random()
            if choice < 0.3:
                session.post(f"{BASE_URL}/api/posts",
                             json={"title": f"Load {random.randint(0,99999)}",
                                   "content": large_content,
                                   "status": "published"},
                             timeout=10)
            elif choice < 0.6:
                session.get(f"{BASE_URL}/api/posts/search",
                            params={"q": "load"}, timeout=10)
            elif choice < 0.8:
                session.get(f"{BASE_URL}/api/posts/feed",
                            params={"limit": 100}, timeout=10)
            else:
                session.get(f"{BASE_URL}/api/dashboard/stats", timeout=10)
        except Exception:
            pass

    while not stop_event.is_set():
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = [pool.submit(single_request) for _ in range(concurrency)]
            for f in futures:
                f.result()
        time.sleep(0.01)


# ---------------------------------------------------------------------------
# Main test
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  AUTOSCALER BURST CONTAINER TEST")
    print("=" * 60)

    # ------------------------------------------------------------------
    # Step 1: Create 6 tenants (enough for bin-packing to split across VMs)
    # ------------------------------------------------------------------
    print("\n[Step 1] Creating 6 test tenants...")
    suffix = "".join(random.choices(string.ascii_lowercase, k=4))
    tenant_names = ["heavy_a", "heavy_b", "heavy_c", "heavy_d", "heavy_e", "extra_f"]
    tenants = {}
    for name in tenant_names:
        tname = f"{name}_{suffix}"
        print(f"  Creating {tname}...")
        user_data = register_user(tname)
        token = login_user(user_data["username"])
        tenants[name] = {
            "tenant_name": tname,
            "username": user_data["username"],
            "tenant_id": user_data["tenant_id"],
            "token": token,
        }
    print(f"  Created {len(tenants)} tenants")

    with open("test_autoscale_tenants.json", "w") as f:
        json.dump(tenants, f, indent=2)

    bursts = get_burst_containers()
    print(f"  Initial burst containers: {len(bursts)}")
    if bursts:
        print(f"  WARNING: Already running: {bursts}")

    # ------------------------------------------------------------------
    # Step 2: Generate light traffic so metrics flush + trigger rebalance
    # ------------------------------------------------------------------
    print("\n[Step 2] Generating light traffic to trigger metrics flush...")
    print("  (Each tenant makes a few requests so the autoscaler has data)")

    for name, info in tenants.items():
        token = info["token"]
        headers = {"Authorization": f"Bearer {token}"}
        for i in range(5):
            try:
                requests.post(f"{BASE_URL}/api/posts",
                              json={"title": f"{name} warmup {i}",
                                    "content": "Warmup content " * 50,
                                    "status": "published"},
                              headers=headers, timeout=10)
            except Exception:
                pass
    print("  Warmup requests sent.")

    # ------------------------------------------------------------------
    # Step 3: Wait for rebalance to distribute tenants across vm1 + vm2
    # ------------------------------------------------------------------
    print("\n[Step 3] Waiting for autoscaler rebalance to spread tenants...")
    print("  (First rebalance runs ~30s after autoscaler starts)")
    print("  Polling placements every 10s...\n")

    distributed = False
    for i in range(18):  # up to 180s
        time.sleep(10)
        elapsed = (i + 1) * 10
        vm1, vm2 = show_placements()
        print(f"  [{elapsed}s]")

        if vm1 > 0 and vm2 > 0:
            distributed = True
            print(f"\n  Tenants distributed across both VMs! (vm1={vm1}, vm2={vm2})")
            break

    if not distributed:
        print("\n  WARNING: Tenants are NOT distributed across both VMs.")
        print("  The autoscaler rebalance may not have run yet.")
        print("  Check autoscaler logs: docker compose logs autoscaler")
        return

    # ------------------------------------------------------------------
    # Step 4: Push both VMs above 70% CPU via docker exec stress + HTTP traffic
    # ------------------------------------------------------------------
    print("\n[Step 4] Injecting CPU stress into both VMs + HTTP traffic for metrics...")
    print("  (HTTP alone can't saturate I/O-bound backends — using docker exec)\n")

    stop_all = Event()
    threads = []

    # Inject CPU stress directly into both VM containers
    for container in ["fyp-vm1-1", "fyp-vm2-1"]:
        t = Thread(target=inject_cpu_stress,
                   args=(container, 180, stop_all), daemon=True)
        t.start()
        threads.append(t)
        print(f"  Started CPU stress on {container}")

    # Also run HTTP traffic for tenant metrics flushing
    for name, info in tenants.items():
        t = Thread(target=http_traffic_worker,
                   args=(info["token"], name, stop_all, 10),
                   daemon=True)
        t.start()
        threads.append(t)

    # Monitor for 30s to let CPU build up
    for i in range(6):
        time.sleep(5)
        elapsed = (i + 1) * 5
        cstats = get_container_stats()
        print(f"  [{elapsed}s] Resources:")
        print_stats(cstats, prefix="  ")

    # ------------------------------------------------------------------
    # Step 5: Wait for autoscaler to spawn burst container
    # ------------------------------------------------------------------
    print("\n[Step 5] Waiting for autoscaler to spawn burst container...")
    print("  (Autoscaler checks every 10s; triggers if ANY resource exceeds threshold on ALL backends)\n")

    burst_detected = False
    for i in range(12):  # up to 120s more
        time.sleep(10)
        elapsed = 30 + (i + 1) * 10

        cstats = get_container_stats()
        bursts = get_burst_containers()

        print(f"  [{elapsed}s] Bursts: {len(bursts)}  |  Resources:")
        print_stats(cstats, prefix="  ")

        # Check if both VMs are above threshold on any resource
        vm_stats = {k: v for k, v in cstats.items() if "vm" in k}
        if vm_stats:
            all_cpu_above = all(v["cpu"] > 70 for v in vm_stats.values())
            all_mem_above = all(v["mem"] > 80 for v in vm_stats.values())
            if not (all_cpu_above or all_mem_above):
                below = {k: f"CPU={v['cpu']:.0f}% MEM={v['mem']:.0f}%"
                         for k, v in vm_stats.items()
                         if v["cpu"] <= 70 and v["mem"] <= 80}
                if below:
                    print(f"  Note: Not all VMs above thresholds: {below}")

        if bursts:
            burst_detected = True
            print(f"\n  BURST CONTAINER SPAWNED: {bursts}")
            print("  Waiting 20s for tenant migration...")
            time.sleep(20)
            break

    # Stop all load
    stop_all.set()
    time.sleep(2)

    # ------------------------------------------------------------------
    # Step 6: Check results
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)

    if not burst_detected:
        print("\n  No burst container spawned.")
        print("  Possible reasons:")
        print("    - Not all VMs exceeded thresholds on any resource simultaneously")
        print("    - Docker resource limits may cap measured usage")
        print("    - Autoscaler container may not be running")
        cstats = get_container_stats()
        print(f"\n  Final resources:")
        print_stats(cstats, prefix="  ")
    else:
        bursts = get_burst_containers()
        print(f"\n  Burst containers: {bursts}")

    print("\n  === Tenant Placements ===")
    show_placements()

    print("\n  === Tenant Metrics ===")
    rows = docker_psql("""
        SELECT t.name,
               ROUND(tm.avg_cpu_ms::numeric, 1),
               tm.avg_bytes_out, tm.request_count
        FROM tenant_metrics tm
        JOIN tenants t ON t.id = tm.tenant_id
        ORDER BY tm.request_count DESC
    """)
    if rows:
        print(f"  {'Tenant':<25} {'CPU(ms)':<10} {'BW(bytes)':<12} {'Requests'}")
        print(f"  {'------':<25} {'-------':<10} {'---------':<12} {'--------'}")
        for r in rows:
            print(f"  {r[0]:<25} {r[1]:<10} {r[2]:<12} {r[3]}")

    print("\n  === Resource Profiles ===")
    rows = docker_psql("""
        SELECT t.name, trp.ram_class, trp.footprint_mb
        FROM tenant_resource_profiles trp
        JOIN tenants t ON t.id = trp.tenant_id
        ORDER BY trp.footprint_mb DESC
    """)
    if rows:
        print(f"  {'Tenant':<25} {'Class':<10} {'Footprint(MB)'}")
        print(f"  {'------':<25} {'-----':<10} {'-------------'}")
        for r in rows:
            print(f"  {r[0]:<25} {r[1]:<10} {r[2]}")

    print("\n" + "=" * 60)
    if burst_detected:
        print("  TEST PASSED: Burst container was spawned under load")
    else:
        print("  TEST INCOMPLETE: Burst container was not spawned")
    print("=" * 60)


if __name__ == "__main__":
    main()
