from analyzer.scanner import iter_files

DOCKERFILE_NAMES = (
    "dockerfile",
)

def detect_dockerfiles(repo):
    """
    Detect Dockerfile existence and locations
    """

    paths = []

    for file in iter_files(repo):
        name = file.name.lower()

        # Dockerfile, Dockerfile.prod, dockerfile.dev, etc.
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
