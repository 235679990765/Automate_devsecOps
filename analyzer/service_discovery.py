from pathlib import Path
from analyzer.language import detect_language


SERVICE_MARKERS = [
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "pom.xml",
    "build.gradle",
    "index.html",
    "go.mod",
    "Cargo.toml"
]


# ---------- HELPERS ----------

def has_service_marker(path: Path) -> bool:
    return any((path / marker).exists() for marker in SERVICE_MARKERS)


def is_go_app(path: Path) -> bool:
    """
    Go is deployable ONLY if it has a real entrypoint.
    """
    for file in path.rglob("main.go"):
        try:
            content = file.read_text(errors="ignore")
            if "package main" in content and "func main" in content:
                return True
        except:
            continue
    return False


def is_node_app(path: Path) -> bool:
    pkg = path / "package.json"
    if not pkg.exists():
        return False
    try:
        content = pkg.read_text(errors="ignore").lower()
        return '"start"' in content
    except:
        return False


def is_python_app(path: Path) -> bool:
    # main.py or FastAPI/Flask app
    if (path / "main.py").exists() or (path / "app.py").exists():
        return True

    for py in path.rglob("*.py"):
        try:
            c = py.read_text(errors="ignore").lower()
            if "fastapi" in c or "flask" in c:
                return True
        except:
            continue
    return False


def is_java_app(path: Path) -> bool:
    pom = path / "pom.xml"
    if not pom.exists():
        return False
    try:
        return "spring" in pom.read_text(errors="ignore").lower()
    except:
        return False


def is_static_app(path: Path) -> bool:
    return (path / "index.html").exists()


def is_deployable(language_info, path: Path) -> bool:
    language = (
        language_info.get("language")
        if isinstance(language_info, dict)
        else language_info
    )

    if language in ["unknown", "react-native", "mobile-react-native"]:
        return False

    if language == "go":
        return is_go_app(path)

    if language == "node":
        return is_node_app(path)

    if language == "python":
        return is_python_app(path)

    if language == "java":
        return is_java_app(path)

    if language == "frontend-static":
        return is_static_app(path)

    # fallback (safe default)
    return False


# ---------- SERVICE DISCOVERY ----------

def discover_services(repo: Path):
    services = []

    # 1️⃣ Root
    if has_service_marker(repo):
        language = detect_language(repo)
        services.append({
            "name": "root",
            "path": repo,
            "language": language,
            "deployable": is_deployable(language, repo)
        })

    # 2️⃣ One level deep
    for item in repo.iterdir():
        if not item.is_dir():
            continue

        if has_service_marker(item):
            language = detect_language(item)
            services.append({
                "name": item.name,
                "path": item,
                "language": language,
                "deployable": is_deployable(language, item)
            })

    return services
