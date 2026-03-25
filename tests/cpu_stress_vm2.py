"""
CPU Stress Script for fyp-vm2-1

Pins the CPU of the fyp-vm2-1 Docker container at ~90% using a feedback loop.
Press Ctrl+C to stop — all stress processes inside the container are cleaned up.

Usage:
    python tests/cpu_stress_vm2.py
"""

import subprocess
import signal
import sys
import time

CONTAINER = "fyp-vm2-1"
TARGET_CPU = 90.0
LOW_THRESHOLD = 85.0
HIGH_THRESHOLD = 95.0
CHECK_INTERVAL = 3  # seconds between CPU checks

# Track all stress subprocess PIDs (host-side Popen objects)
stress_procs: list[subprocess.Popen] = []


def get_cpu_percent() -> float:
    """Read current CPU% of the container via docker stats."""
    try:
        result = subprocess.run(
            ["docker", "stats", CONTAINER, "--no-stream", "--format", "{{.CPUPerc}}"],
            capture_output=True, text=True, timeout=10,
        )
        raw = result.stdout.strip().replace("%", "")
        return float(raw) if raw else 0.0
    except Exception as e:
        print(f"  Warning: could not read CPU stats: {e}")
        return 0.0


def spawn_stress_worker():
    """Start one CPU-burn process inside the container."""
    proc = subprocess.Popen(
        [
            "docker", "exec", CONTAINER,
            "python", "-c",
            "while True:\n [x**2 for x in range(10000)]",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    stress_procs.append(proc)
    print(f"  + Spawned worker (total: {len(stress_procs)})")


def kill_one_worker():
    """Kill the most recently added stress worker."""
    if not stress_procs:
        return
    proc = stress_procs.pop()
    proc.terminate()
    proc.wait(timeout=5)
    print(f"  - Killed worker (total: {len(stress_procs)})")


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
             "  if 'x**2' in c:\n"
             "   os.kill(pid,signal.SIGKILL)\n"
             " except: pass\n"],
            timeout=10, capture_output=True,
        )
    except Exception as e:
        print(f"  Warning: could not kill container processes: {e}")


def cleanup_all():
    """Kill all stress workers — both host-side and inside the container."""
    print("\nCleaning up stress workers...")
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
    print("All stress workers stopped.")


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

    print(f"Targeting ~{TARGET_CPU:.0f}% CPU on {CONTAINER}")
    print(f"Thresholds: add worker < {LOW_THRESHOLD:.0f}%, remove worker > {HIGH_THRESHOLD:.0f}%")
    print("Press Ctrl+C to stop.\n")

    # Start with 2 workers to ramp up quickly
    spawn_stress_worker()
    spawn_stress_worker()

    try:
        while True:
            time.sleep(CHECK_INTERVAL)
            cpu = get_cpu_percent()
            print(f"  CPU: {cpu:.1f}%  |  Workers: {len(stress_procs)}")

            if cpu < LOW_THRESHOLD and len(stress_procs) < 10:
                spawn_stress_worker()
            elif cpu > HIGH_THRESHOLD and len(stress_procs) > 1:
                kill_one_worker()
    except KeyboardInterrupt:
        pass
    finally:
        cleanup_all()


if __name__ == "__main__":
    main()
