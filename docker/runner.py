import subprocess
import random
from pathlib import Path

from docker.env import write_env_file
from docker.utils import image_exists, pull_image
from docker.builder import build_image


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
# FINAL RUNNER (AUTO BUILD + SAFE RUN)
# ------------------------------
def run_container(
    image: str,
    container_port: int,
    project: str,
    service_path: Path,
    repo_root: Path,
    env_vars: dict | None = None
):
    """
    FINAL RULES:
    - Auto-pull or auto-build image if missing
    - Reuse container if same image exists
    - Never bind host port 80
    - Inject env vars via .env
    """

    # 🔹 Write env file if provided
    env_file = write_env_file(service_path, env_vars or {})

    # 🔥 ENSURE IMAGE EXISTS (FIX FOR YOUR ERROR)
    if not image_exists(image):
        pulled = pull_image(image)
        if not pulled:
            build_image(
                repo_root=repo_root,
                service={"path": service_path.name},
                image=image
            )

    # 🔁 Reuse existing container
    existing_cid = get_container_by_image(image)
    if existing_cid:
        if not is_container_running(existing_cid):
            subprocess.run(["docker", "start", existing_cid], check=True)
            print(f"🔄 Restarted container with existing port")

        host_port = get_container_host_port(existing_cid, container_port)
        return {
            "status": "reused",
            "url": f"http://localhost:{host_port}",
            "port": host_port
        }

    # 🔥 Check if any old container for this project exists to reuse its port
    try:
        old_containers = subprocess.check_output(
            [
                "docker", "ps", "-a",
                "--filter", f"label=devsecops.project={project}",
                "--format", "{{.ID}}"
            ]
        ).decode().strip().splitlines()
        
        # Try to reuse port from first existing container
        if old_containers:
            old_port = get_container_host_port(old_containers[0], container_port)
            if old_port:
                host_port = old_port
                print(f"♻️  Reusing port {host_port} from previous container")
            else:
                host_port = container_port
        else:
            host_port = container_port
    except:
        host_port = container_port

    # 🔒 Decide host port if not reused
    if host_port == container_port:
        if container_port == 80 or not is_port_free(container_port):
            host_port = random.randint(30000, 40000)
            print(f"⚠️  Port {container_port} unavailable, using {host_port}")
        else:
            host_port = container_port
            print(f"✅ Using port {host_port}")

    # 🔥 Stop old containers
    stop_all_project_containers(project)

    container_name = image.replace("/", "_").replace(":", "_")

    # � Remove old container with same name if exists
    try:
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            check=False,
            capture_output=True
        )
    except subprocess.CalledProcessError:
        pass

    # �🔹 Build docker run command
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
