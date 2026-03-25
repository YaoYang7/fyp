"""
Bandwidth Stress Script for fyp-vm1-1

Generates sustained TX network traffic (~60 MB/s) from the fyp-vm1-1 container
to exceed the autoscaler's BW_THRESHOLD (50 MB/s).
Press Ctrl+C to stop.

Usage:
    python tests/bw_stress_vm1.py
"""

import subprocess
import signal
import sys
import time

CONTAINER = "fyp-vm1-1"
TARGET_MBPS = 60  # MB/s TX — above the 50 MB/s threshold
CHECK_INTERVAL = 3
NUM_WORKERS = 4  # parallel traffic generators

stress_procs: list[subprocess.Popen] = []


def get_net_io() -> str:
    """Read current network I/O of the container via docker stats."""
    try:
        result = subprocess.run(
            ["docker", "stats", CONTAINER, "--no-stream", "--format", "{{.NetIO}}"],
            capture_output=True, text=True, timeout=10,
        )
        return result.stdout.strip()
    except Exception as e:
        return f"(could not read: {e})"


def spawn_traffic_worker():
    """Start one network traffic generator inside the container.

    Uses Python to send large UDP packets to a discard target (localhost:9).
    UDP to port 9 (discard) avoids needing a listener and still generates
    real TX bytes counted by Docker's network stats.
    """
    # Each worker sends ~15 MB/s of UDP traffic
    chunk_kb = 64  # 64KB per packet (max UDP-safe size)
    script = (
        "import socket, time\n"
        "s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)\n"
        f"chunk = b'x' * ({chunk_kb} * 1024)\n"
        "while True:\n"
        "    try:\n"
        "        s.sendto(chunk, ('127.0.0.1', 9))\n"
        "    except Exception:\n"
        "        time.sleep(0.001)\n"
    )
    proc = subprocess.Popen(
        ["docker", "exec", CONTAINER, "python", "-c", script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    stress_procs.append(proc)
    print(f"  + Spawned traffic worker (total: {len(stress_procs)})")


def kill_one_worker():
    """Kill the most recently added traffic worker."""
    if not stress_procs:
        return
    proc = stress_procs.pop()
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
    print(f"  - Killed traffic worker (total: {len(stress_procs)})")


def kill_container_stress_processes():
    """Kill all stress Python processes running inside the container via /proc."""
    try:
        subprocess.run(
            ["docker", "exec", CONTAINER, "python", "-c",
             "import os,signal\n"
             "for d in os.listdir('/proc'):\n"
             " if not d.isdigit(): continue\n"
             " pid=int(d)\n"
             " if pid==1 or pid==os.getpid(): continue\n"
             " try:\n"
             "  c=open(f'/proc/{pid}/cmdline','rb').read().decode('utf-8','replace')\n"
             "  if 'sendto' in c or 'SOCK_DGRAM' in c:\n"
             "   os.kill(pid,signal.SIGKILL)\n"
             " except: pass\n"],
            timeout=10, capture_output=True,
        )
    except Exception as e:
        print(f"  Warning: could not kill container processes: {e}")


def cleanup_all():
    """Kill all traffic workers — both host-side and inside the container."""
    print("\nCleaning up traffic workers...")
    for proc in stress_procs:
        try:
            proc.terminate()
        except Exception:
            pass
    for proc in stress_procs:
        try:
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    stress_procs.clear()
    kill_container_stress_processes()
    print("All traffic workers stopped.")


def signal_handler(sig, frame):
    cleanup_all()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def main():
    # Verify container is running
    result = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", CONTAINER],
        capture_output=True, text=True,
    )
    if "true" not in result.stdout.lower():
        print(f"Error: container {CONTAINER} is not running.")
        sys.exit(1)

    print(f"Generating ~{TARGET_MBPS} MB/s TX bandwidth on {CONTAINER}")
    print(f"Workers: {NUM_WORKERS} (UDP to localhost:9 discard)")
    print("Press Ctrl+C to stop.\n")

    for _ in range(NUM_WORKERS):
        spawn_traffic_worker()

    try:
        while True:
            time.sleep(CHECK_INTERVAL)
            net_io = get_net_io()
            alive = sum(1 for p in stress_procs if p.poll() is None)
            print(f"  Net I/O: {net_io}  |  Workers alive: {alive}/{len(stress_procs)}")

            # Restart any dead workers
            for i, proc in enumerate(stress_procs):
                if proc.poll() is not None:
                    print(f"  Restarting dead worker {i}...")
                    stress_procs[i] = subprocess.Popen(
                        ["docker", "exec", CONTAINER, "python", "-c",
                         "import socket,time\n"
                         "s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)\n"
                         "chunk=b'x'*(64*1024)\n"
                         "while True:\n"
                         " try: s.sendto(chunk,('127.0.0.1',9))\n"
                         " except: time.sleep(0.001)\n"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
    except KeyboardInterrupt:
        pass
    finally:
        cleanup_all()


if __name__ == "__main__":
    main()
