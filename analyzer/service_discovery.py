from pathlib import Path
from analyzer.language import detect_language

SERVICE_MARKERS = [
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "pom.xml",
    "build.gradle",
    "index.html"
]

def has_service_marker(path: Path) -> bool:
    return any((path / marker).exists() for marker in SERVICE_MARKERS)


def is_deployable(language: str) -> bool:
    if language in ["unknown", "react-native", "mobile-react-native"]:
        return False
    return True


def discover_services(repo: Path):
    services = []

    # 1️⃣ Check root as a service
    if has_service_marker(repo):
        language = detect_language(repo)
        services.append({
            "name": "root",
            "path": repo,
            "language": language,
            "deployable": is_deployable(language)
        })

    # 2️⃣ Scan one level deep ALWAYS
    for item in repo.iterdir():
        if not item.is_dir():
            continue

        if has_service_marker(item):
            language = detect_language(item)
            services.append({
                "name": item.name,
                "path": item,
                "language": language,
                "deployable": is_deployable(language)
            })

    return services