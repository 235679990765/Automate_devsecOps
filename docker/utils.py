import re

def sanitize_image_name(name: str) -> str:
    """
    Docker image names must be lowercase and valid.
    """
    name = name.lower()
    name = re.sub(r"[^a-z0-9._-]", "-", name)
    return name
