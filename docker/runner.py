import subprocess
import random
from pathlib import Path
from docker.env import write_env_file


# ------------------------------
# Find container by image
# ------------------------------
def get_container_by_image(image: str):
    try:
        cid = subprocess.check_output(
            ["docker", "ps", "-a", "--filter", f"ancestor={image}", "--format", "{{.ID}}"]
        ).decode().strip()
        return cid if cid else None
    except subprocess.CalledProcessError:
        return None


def is_container_running(container_id: str) -> bool:
    try:
        status = subprocess.check_output(
            ["docker", "inspect", "-f", "{{.State.Running}}", container_id]
        ).decode().strip()
        return status == "true"
    except subprocess.CalledProcessError:
        return False


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


def is_port_free(port: int) -> bool:
    try:
        out = subprocess.check_output(
            ["docker", "ps", "--filter", f"publish={port}", "--format", "{{.ID}}"]
        ).decode().strip()
        return out == ""
    except subprocess.CalledProcessError:
        return True


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


# ------------------------------
# FINAL RUNNER (ENV + PORT SAFE)
# ------------------------------
def run_container(
    image: str,
    container_port: int,
    project: str,
    service_path: Path,
    env_vars: dict | None = None
):
    """
    FINAL RULES:
    - Reuse container if same image exists
    - Never bind host port 80
    - Inject env vars via .env
    """

    # 🔹 Write env file if provided
    env_file = write_env_file(service_path, env_vars or {})

    # 🔁 Reuse existing container
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

    # 🔥 New image → stop old containers
    stop_all_project_containers(project)

    # 🔒 Decide host port
    if container_port == 80 or not is_port_free(container_port):
        host_port = random.randint(30000, 40000)
    else:
        host_port = container_port

    container_name = image.replace("/", "_").replace(":", "_")

    # 🔹 Build docker run command
    cmd = [
        "docker", "run", "-d",
        "--name", container_name,
        "--label", f"devsecops.project={project}",
        "-p", f"{host_port}:{container_port}"
    ]

    if env_file:
        cmd += ["--env-file", str(env_file)]

    cmd.append(image)

    subprocess.run(cmd, check=True)

    return {
        "status": "running",
        "url": f"http://localhost:{host_port}",
        "port": host_port
    }
