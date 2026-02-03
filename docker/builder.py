import subprocess
from pathlib import Path
from docker.generator import generate_dockerfile


def build_image(repo_root: Path, service: dict, image: str):
    """
    Guarantees Dockerfile exists inside build context,
    then builds the image safely.
    """

    service_path = repo_root / service["path"]
    dockerfile_path = service_path / "Dockerfile"

    # 🔥 Ensure Dockerfile exists
    if not dockerfile_path.exists():
        generate_dockerfile(
            service_path=service_path,
            analysis=service.get("analysis", {})
        )

    # 🔥 Explicit Dockerfile path (Windows-safe)
    cmd = [
        "docker", "build",
        "-t", image,
        "-f", str(dockerfile_path),
        str(service_path),
    ]

    subprocess.run(cmd, check=True)

    return {
        "status": "built",
        "image": image,
    }
