import subprocess
import random


# ---------------------------------------------------------
# Find container (running or stopped) by image
# ---------------------------------------------------------
def get_container_by_image(image: str):
    try:
        cid = subprocess.check_output(
            [
                "docker", "ps", "-a",
                "--filter", f"ancestor={image}",
                "--format", "{{.ID}}"
            ]
        ).decode().strip()
        return cid if cid else None
    except subprocess.CalledProcessError:
        return None


# ---------------------------------------------------------
# Check if container is running
# ---------------------------------------------------------
def is_container_running(container_id: str) -> bool:
    try:
        status = subprocess.check_output(
            [
                "docker", "inspect",
                "-f", "{{.State.Running}}",
                container_id
            ]
        ).decode().strip()
        return status == "true"
    except subprocess.CalledProcessError:
        return False


# ---------------------------------------------------------
# Get actual HOST port mapped to container port
# ---------------------------------------------------------
def get_container_host_port(container_id: str, container_port: int):
    try:
        out = subprocess.check_output(
            [
                "docker", "inspect",
                "-f",
                f"{{{{(index (index .NetworkSettings.Ports \"{container_port}/tcp\") 0).HostPort}}}}",
                container_id
            ]
        ).decode().strip()
        return int(out) if out else None
    except subprocess.CalledProcessError:
        return None


# ---------------------------------------------------------
# Check if a host port is free
# ---------------------------------------------------------
def is_port_free(port: int) -> bool:
    try:
        out = subprocess.check_output(
            ["docker", "ps", "--filter", f"publish={port}", "--format", "{{.ID}}"]
        ).decode().strip()
        return out == ""
    except subprocess.CalledProcessError:
        return True


# ---------------------------------------------------------
# Stop all containers belonging to this project
# ---------------------------------------------------------
def stop_all_project_containers(project: str):
    try:
        container_ids = subprocess.check_output(
            [
                "docker", "ps", "-a",
                "--filter", f"label=devsecops.project={project}",
                "--format", "{{.ID}}"
            ]
        ).decode().strip().splitlines()

        for cid in container_ids:
            subprocess.run(["docker", "stop", cid], check=True)
    except subprocess.CalledProcessError:
        pass


# ---------------------------------------------------------
# SMART PLATFORM-GRADE RUNNER (FINAL)
# ---------------------------------------------------------
def run_container(image: str, container_port: int, project: str):
    """
    FINAL RULES:
    - Reuse container if same image exists
    - If container exposes port 80 → ALWAYS use random host port
    - Otherwise use fixed port if free
    - Never crash on port conflicts
    """

    # 1️⃣ Reuse existing container
    existing_cid = get_container_by_image(image)
    if existing_cid:
        if not is_container_running(existing_cid):
            subprocess.run(["docker", "start", existing_cid], check=True)

        host_port = get_container_host_port(existing_cid, container_port)

        return {
            "status": "reused",
            "url": f"http://localhost:{host_port}",
            "port": host_port
        }

    # 2️⃣ New image → stop old project containers
    stop_all_project_containers(project)

    # 3️⃣ Decide host port (CRITICAL FIX)
    if container_port == 80:
        # 🔒 NEVER bind 80 directly
        host_port = random.randint(30000, 40000)
    else:
        if is_port_free(container_port):
            host_port = container_port
        else:
            host_port = random.randint(30000, 40000)

    container_name = image.replace("/", "_").replace(":", "_")

    # 4️⃣ Run container
    cmd = [
        "docker", "run", "-d",
        "--name", container_name,
        "--label", f"devsecops.project={project}",
        "-p", f"{host_port}:{container_port}",
        image
    ]

    subprocess.run(cmd, check=True)

    return {
        "status": "running",
        "url": f"http://localhost:{host_port}",
        "port": host_port
    }
