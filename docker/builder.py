import subprocess
from pathlib import Path

def build_image(repo_root: Path, service: dict, image: str):
    service_path = repo_root / service["path"]
    dockerfile = service_path / "Dockerfile"

    if not dockerfile.exists():
        return {"status": "skipped", "reason": "Dockerfile missing"}

    cmd = [
        "docker", "build",
        "-t", image,
        "-f", str(dockerfile),
        str(service_path)
    ]

    subprocess.run(cmd, check=True)
    return {"status": "built", "image": image}
