from pathlib import Path


def detect_dockerfiles(repo: Path):
    """
    Detect Dockerfile existence and locations (case-insensitive).
    This searches for files named `Dockerfile` or starting with `Dockerfile.`
    so files with no extension are detected even when `iter_files` filters
    by extension.
    """

    paths = []

    for file in repo.rglob("*"):
        if not file.is_file():
            continue

        name = file.name.lower()
        if name == "dockerfile" or name.startswith("dockerfile."):
            paths.append(str(file))

    return {
        "exists": bool(paths),
        "count": len(paths),
        "paths": paths,
        "scope": _detect_scope(paths)
    }


def _detect_scope(paths):
    """
    Determine if Dockerfiles are root-level or service-level
    """
    if not paths:
        return None

    if all(p.count("/") == 1 or p.count("\\") == 1 for p in paths):
        return "root"

    return "service"
