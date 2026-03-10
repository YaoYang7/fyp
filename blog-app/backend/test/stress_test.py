"""
stress_test.py — Selenium-based demo of load balancer and autoscaler.

Requirements:
    pip install selenium

Usage:
    python stress_test.py          # both phases
    python stress_test.py lb       # load balancer only
    python stress_test.py scale    # autoscaler only

Exit codes:
    0 — all tests passed
    1 — one or more tests failed
"""

import sys
import time
import threading
import subprocess
import urllib.request
from collections import Counter

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

BASE = "http://localhost"

# /api/ endpoints proxy to the backend containers (X-Served-By is set there).
# GET / proxies to the frontend nginx — no X-Served-By header there.
LB_PROBE   = f"{BASE}/api/posts/feed"
API_URLS   = [f"{BASE}/api/posts/feed", f"{BASE}/api/posts/recent", f"{BASE}/"]

# Backend container names (as created by docker-compose)
BACKENDS = ["fyp-lightweight-backend-1", "fyp-heavyweight-backend-1"]


# ── helpers ───────────────────────────────────────────────────────────────────

def make_driver(headless=True):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,720")
    return webdriver.Chrome(options=opts)


def containers():
    out = subprocess.check_output(
        ["docker", "ps", "--format", "{{.Names}}"], text=True
    )
    return sorted(out.strip().splitlines())


def autoscaler_tail(n=3):
    out = subprocess.check_output(
        ["docker", "logs", "--tail", str(n), "fyp-autoscaler-1"],
        text=True, stderr=subprocess.STDOUT,
    )
    return out.strip()


def check(label, passed, detail=""):
    icon = "PASS" if passed else "FAIL"
    msg = f"  [{icon}] {label}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    return passed


# ── Phase 1: Load Balancer ────────────────────────────────────────────────────

def test_lb(n=20, delay=0.3):
    print("\n" + "=" * 60)
    print("PHASE 1 — Load Balancer")
    print(f"  {n} requests to {LB_PROBE}  (nginx DNS TTL = 5s)")
    print("=" * 60)
    failures = []

    # 1a. Open a visible browser to show the app works end-to-end
    print("\n[1] Opening Chrome to verify the app loads …")
    driver = make_driver(headless=False)
    page_loaded = False
    try:
        driver.get(BASE)
        time.sleep(3)
        title = driver.title
        page_loaded = bool(title) or "localhost" in driver.current_url
        print(f"    Page title: '{title}'")
    except Exception as e:
        print(f"    ERROR: {e}")
    finally:
        driver.quit()

    if not check("App loads in Chrome", page_loaded):
        failures.append("App did not load in browser")

    # 1b. Hit an /api/ endpoint — nginx routes these to backend:8000 and sets
    #     X-Served-By to the upstream IP, which rotates between the two backends.
    print(f"\n[2] Sending {n} requests to {LB_PROBE} …\n")
    counts = Counter()
    errors = 0
    for i in range(1, n + 1):
        try:
            with urllib.request.urlopen(LB_PROBE, timeout=10) as r:
                served_by = r.headers.get("X-Served-By", "unknown")
                print(f"  req {i:>2}: HTTP {r.status}  →  {served_by}")
                counts[served_by] += 1
        except urllib.error.HTTPError as e:
            # A 4xx/5xx still has headers — read X-Served-By from the error
            served_by = e.headers.get("X-Served-By", "unknown")
            print(f"  req {i:>2}: HTTP {e.code}  →  {served_by}")
            counts[served_by] += 1
        except Exception as e:
            print(f"  req {i:>2}: ERROR — {e}")
            errors += 1
        time.sleep(delay)

    total = sum(counts.values())
    unique_backends = len(counts)
    max_share = max(counts.values()) / total * 100 if total else 100

    print("\nDistribution summary:")
    for addr, cnt in counts.most_common():
        pct = cnt / total * 100 if total else 0
        bar = "█" * cnt
        print(f"  {addr:<35} {cnt:>3}/{total}  ({pct:.0f}%)  {bar}")

    print()
    if not check("No connection errors", errors == 0, f"{errors} errors"):
        failures.append(f"{errors} connection errors")
    if not check("Requests spread across ≥2 backends", unique_backends >= 2,
                 f"{unique_backends} backend(s) seen"):
        failures.append("Requests not distributed — only 1 backend responded")
    if not check("No backend handles >80% of traffic", max_share <= 80,
                 f"top backend: {max_share:.0f}%"):
        failures.append(f"Uneven distribution — top backend at {max_share:.0f}%")

    return failures


# ── Phase 2: Autoscaler ───────────────────────────────────────────────────────
# CPU stress is injected directly into each backend container via docker exec.
# HTTP flooding alone (even at high concurrency) barely moves the CPU because
# the Python/FastAPI workers are mostly I/O-bound on DB queries.

def _cpu_stress(container, duration):
    """Run a CPU-bound Python loop inside a container for `duration` seconds."""
    subprocess.run([
        "docker", "exec", container,
        "python", "-c",
        f"import time; e=time.time()+{duration}\n"
        f"while time.time()<e: [x**2 for x in range(10000)]",
    ])


def _browser_worker(idx, stop_flag):
    """Headless Chrome session that continuously reloads the app."""
    driver = None
    try:
        driver = make_driver(headless=True)
        while not stop_flag.is_set():
            try:
                driver.get(BASE + "/")
                time.sleep(0.5)
            except Exception:
                pass
    except Exception as e:
        print(f"  [browser-{idx}] init error: {e}")
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def _api_worker(idx, stop_flag):
    """Direct HTTP flood to backend API endpoints."""
    i = idx
    while not stop_flag.is_set():
        try:
            with urllib.request.urlopen(API_URLS[i % len(API_URLS)], timeout=5) as r:
                r.read()
        except Exception:
            pass
        i += 1


def test_autoscaler(browser_sessions=5, api_workers=20, duration=90):
    print("\n" + "=" * 60)
    print(f"PHASE 2 — Autoscaler")
    print(f"  CPU stress via docker exec  +  {browser_sessions} Selenium sessions"
          f"  +  {api_workers} API threads  ×  {duration}s")
    print("  Scale-up  threshold : 70% CPU on ALL backends")
    print("  Scale-down threshold: 30% CPU, 60 s cooldown")
    print("=" * 60)
    failures = []

    baseline = set(containers())
    print(f"\n[t=0s]  baseline containers ({len(baseline)}): {sorted(baseline)}\n")

    stop_flag = threading.Event()

    # Stress each backend container's CPU directly
    stress_threads = [
        threading.Thread(target=_cpu_stress, args=(c, duration), daemon=True)
        for c in BACKENDS
    ]
    # Browser sessions for visual demo
    browser_threads = [
        threading.Thread(target=_browser_worker, args=(i, stop_flag), daemon=True)
        for i in range(browser_sessions)
    ]
    # API flood threads for realistic HTTP load
    api_threads = [
        threading.Thread(target=_api_worker, args=(i, stop_flag), daemon=True)
        for i in range(api_workers)
    ]

    all_threads = stress_threads + browser_threads + api_threads
    print("Starting CPU stress + load …\n")
    for t in all_threads:
        t.start()

    start = time.time()
    peak_containers = set(baseline)

    for cp in range(10, duration + 1, 10):
        delay = cp - (time.time() - start)
        if delay > 0:
            time.sleep(delay)
        elapsed = int(time.time() - start)
        current = set(containers())
        peak_containers |= current
        print(f"[t={elapsed:>3}s]  containers ({len(current)}): {sorted(current)}")
        print(f"         autoscaler: {autoscaler_tail(2)}\n")

    stop_flag.set()
    for t in all_threads:
        t.join(timeout=15)

    burst_seen = peak_containers - baseline
    elapsed = int(time.time() - start)
    print(f"\n[t={elapsed}s]  Load stopped.")
    print(f"  Burst containers observed during flood: {burst_seen or 'none'}")

    print()
    if not check("Autoscaler spawned ≥1 burst container", len(burst_seen) >= 1,
                 f"seen: {burst_seen or 'none'}"):
        failures.append("No burst containers spawned — CPU may not have exceeded 70%")

    # Wait for scale-down
    print("\nWaiting for scale-down (up to 70 s) …\n")
    start2 = time.time()
    final_containers = set(containers())
    for _ in range(7):
        time.sleep(10)
        elapsed2 = int(time.time() - start2)
        final_containers = set(containers())
        print(f"[t={elapsed2:>3}s cooldown]  containers ({len(final_containers)}): {sorted(final_containers)}")

    remaining_burst = final_containers - baseline
    print()
    if not check("Burst containers removed after cooldown", len(remaining_burst) == 0,
                 f"still running: {remaining_burst}" if remaining_burst else "all removed"):
        failures.append(f"Burst containers not removed after cooldown: {remaining_burst}")

    return failures


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "both"
    all_failures = []

    if mode in ("lb", "both"):
        all_failures += test_lb(n=20, delay=0.3)
    if mode in ("scale", "both"):
        all_failures += test_autoscaler(browser_sessions=5, api_workers=20, duration=90)

    print("\n" + "=" * 60)
    if all_failures:
        print(f"RESULT: FAILED ({len(all_failures)} assertion(s) failed)")
        for f in all_failures:
            print(f"  x {f}")
        sys.exit(1)
    else:
        print("RESULT: PASSED — all assertions met")
        sys.exit(0)
