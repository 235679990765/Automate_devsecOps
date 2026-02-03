import subprocess
import re

def sanitize_image_name(name: str) -> str:
    name = name.lower()
    return re.sub(r"[^a-z0-9._/-]", "-", name)


def image_exists(image: str) -> bool:
    return subprocess.run(
        ["docker", "image", "inspect", image],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    ).returncode == 0


def pull_image(image: str) -> bool:
    return subprocess.run(
        ["docker", "pull", image],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    ).returncode == 0
