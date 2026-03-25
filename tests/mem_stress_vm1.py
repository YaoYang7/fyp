"""
Memory Stress Script for fyp-vm1-1

Pins memory usage of the fyp-vm1-1 Docker container at ~90% (≈922MB of 1024MB limit).
Press Ctrl+C to stop — the stress process inside the container is cleaned up.

Usage:
    python tests/mem_stress_vm1.py
"""

import subprocess
import signal
import sys
import time

CONTAINER = "fyp-vm1-1"
MEM_LIMIT_MB = 1024
TARGET_PERCENT = 90
TARGET_MB = int(MEM_LIMIT_MB * TARGET_PERCENT / 100)  # ~922MB
CHECK_INTERVAL = 3

stress_proc: subprocess.Popen | None = None


def get_mem_usage() -> str:
    """Read current memory usage of the container via docker stats."""
    try:
        result = subprocess.run(
            ["docker", "stats", CONTAINER, "--no-stream", "--format", "{{.MemUsage}} | {{.MemPerc}}"],
            capture_output=True, text=True, timeout=10,
        )
        return result.stdout.strip()
    except Exception as e:
        return f"(could not read: {e})"


def start_stress():
    """Allocate ~TARGET_MB inside the container and hold it."""
    global stress_proc
    # Allocate memory in 1MB chunks, then hold forever
    script = (
        f"import time\n"
        f"blocks = []\n"
        f"for i in range({TARGET_MB}):\n"
        f"    blocks.append(b'x' * (1024 * 1024))\n"
        f"    if i % 50 == 0:\n"
        f"        print(f'Allocated {{i+1}}MB / {TARGET_MB}MB', flush=True)\n"
        f"print(f'Holding {TARGET_MB}MB. Waiting...', flush=True)\n"
        f"while True:\n"
        f"    time.sleep(60)\n"
    )
    stress_proc = subprocess.Popen(
        ["docker", "exec", CONTAINER, "python", "-c", script],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    print(f"  Allocating ~{TARGET_MB}MB inside {CONTAINER}...")


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
             "  if 'blocks' in c or 'Allocated' in c:\n"
             "   os.kill(pid,signal.SIGKILL)\n"
             " except: pass\n"],
            timeout=10, capture_output=True,
        )
    except Exception as e:
        print(f"  Warning: could not kill container processes: {e}")


def cleanup():
    """Kill the stress process — both host-side and inside the container."""
    global stress_proc
    print("\nCleaning up...")
    if stress_proc:
        try:
            stress_proc.terminate()
            stress_proc.wait(timeout=5)
        except Exception:
            try:
                stress_proc.kill()
            except Exception:
                pass
        stress_proc = None
    kill_container_stress_processes()
    print("Memory stress stopped.")


def signal_handler(sig, frame):
    cleanup()
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

    print(f"Targeting ~{TARGET_PERCENT}% memory ({TARGET_MB}MB / {MEM_LIMIT_MB}MB) on {CONTAINER}")
    print("Press Ctrl+C to stop.\n")

    start_stress()

    try:
        while True:
            time.sleep(CHECK_INTERVAL)
            mem = get_mem_usage()
            status = "allocating..." if stress_proc and stress_proc.poll() is None else "process exited"
            print(f"  Mem: {mem}  |  Status: {status}")

            # If the process died (e.g. OOM killed), restart with less
            if stress_proc and stress_proc.poll() is not None:
                print("  Stress process exited (possibly OOM). Restarting...")
                start_stress()
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()


if __name__ == "__main__":
    main()
