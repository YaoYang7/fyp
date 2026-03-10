import docker
import os
import time

low_api = docker.APIClient(base_url="unix:///var/run/docker.sock")

CPU_THRESHOLD       = float(os.getenv("CPU_THRESHOLD", "70"))
SCALE_DOWN_THRESH   = float(os.getenv("SCALE_DOWN_THRESHOLD", "30"))
SCALE_DOWN_COOLDOWN = int(os.getenv("SCALE_DOWN_COOLDOWN", "60"))
CHECK_INTERVAL      = int(os.getenv("CHECK_INTERVAL", "10"))
MAX_BURST           = int(os.getenv("MAX_BURST", "3"))
NETWORK_NAME        = os.getenv("NETWORK_NAME", "fyp_blog_net")
UPLOADS_VOLUME      = os.getenv("UPLOADS_VOLUME", "fyp_uploads_data")
BURST_IMAGE         = os.getenv("BURST_IMAGE", "blog-backend:latest")
DATABASE_URL        = os.getenv("DATABASE_URL")
JWT_SECRET_KEY      = os.getenv("JWT_SECRET_KEY")
CORS_ORIGINS        = os.getenv("CORS_ORIGINS", "http://localhost")

burst_containers = []  # list of container IDs spawned by the autoscaler
burst_count      = 0
all_idle_since   = None  # timestamp when all backends first dropped below threshold


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


def get_cpu_percent(container_id):
    """Return CPU usage % relative to the container's allocated CPU limit.

    Uses container-relative percentage so that a container running at full
    capacity always reads ~100% regardless of how many CPUs the host has.
    Formula: (cpu_delta / sys_delta) * (host_cpus / cpu_limit) * 100
    """
    try:
        stats = low_api.stats(container_id, stream=False)
        cpu_delta = (
            stats["cpu_stats"]["cpu_usage"]["total_usage"]
            - stats["precpu_stats"]["cpu_usage"]["total_usage"]
        )
        sys_delta = (
            stats["cpu_stats"]["system_cpu_usage"]
            - stats["precpu_stats"]["system_cpu_usage"]
        )
        num_cpus = stats["cpu_stats"].get("online_cpus", 1)
        if sys_delta <= 0:
            return 0.0
        # NanoCpus is the CPU limit in billionths of a CPU (0 = no limit).
        ctr_info = low_api.inspect_container(container_id)
        nano_cpus = ctr_info["HostConfig"].get("NanoCpus", 0)
        cpu_limit = nano_cpus / 1e9 if nano_cpus > 0 else num_cpus
        return (cpu_delta / sys_delta) * (num_cpus / cpu_limit) * 100.0
    except Exception as e:
        print(f"[AUTOSCALER] CPU error for {container_id}: {e}")
        return 0.0


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


print(f"[AUTOSCALER] Started — thresholds: up>{CPU_THRESHOLD}% / down<{SCALE_DOWN_THRESH}% "
      f"for {SCALE_DOWN_COOLDOWN}s, max_burst={MAX_BURST}, check_interval={CHECK_INTERVAL}s")

while True:
    ids = get_backend_container_ids()

    if not ids:
        print("[AUTOSCALER] No backend containers found on network yet, retrying...")
        time.sleep(CHECK_INTERVAL)
        continue

    cpus = {cid: get_cpu_percent(cid) for cid in ids}
    for cid, pct in cpus.items():
        print(f"[AUTOSCALER]   {cid}: CPU={pct:.1f}%")

    all_full = all(pct > CPU_THRESHOLD for pct in cpus.values())
    all_idle = all(pct < SCALE_DOWN_THRESH for pct in cpus.values())

    if all_full:
        all_idle_since = None
        if len(burst_containers) < MAX_BURST:
            spawn_burst()
        else:
            print(f"[AUTOSCALER] All backends full but MAX_BURST={MAX_BURST} already reached")

    elif all_idle and burst_containers:
        now = time.time()
        if all_idle_since is None:
            all_idle_since = now
            remaining = SCALE_DOWN_COOLDOWN
            print(f"[AUTOSCALER] All backends idle — will scale down in {remaining}s if load stays low")
        elif now - all_idle_since >= SCALE_DOWN_COOLDOWN:
            remove_burst()
            all_idle_since = None  # reset: wait another full cooldown before next removal

    else:
        if all_idle_since is not None:
            print("[AUTOSCALER] Load increased again, cancelling scale-down")
        all_idle_since = None

    time.sleep(CHECK_INTERVAL)
