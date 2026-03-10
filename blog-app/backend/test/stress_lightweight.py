"""
stress_lightweight.py — Infinite CPU stress on fyp-lightweight-backend-1.
Ctrl+C to stop.
"""
import subprocess, sys

container = "fyp-lightweight-backend-1"
print(f"Starting infinite CPU stress on {container} ... (Ctrl+C to stop)")
try:
    subprocess.run([
        "docker", "exec", container,
        "python", "-c",
        "while True:\n    [x**2 for x in range(10000000)]",
    ])
except KeyboardInterrupt:
    print(f"\nStopped stress on {container}.")
    sys.exit(0)
