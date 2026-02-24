from pathlib import Path

IGNORED_DIRS = {
    "node_modules",
    ".git",
    "venv",
    ".venv",
    "__pycache__",
    "dist",
    "build",
}


def safe_scan_python_files(repo: Path, max_files: int = 25):
    """Scan limited python files for framework detection"""
    count = 0
    for f in repo.rglob("*.py"):
        if any(part in IGNORED_DIRS for part in f.parts):
            continue

        yield f
        count += 1
        if count >= max_files:  # 🚀 performance guard
            break


def detect_language(repo: Path):
    """
    Returns:
    {
      "language": str,
      "framework": str | None
    }
    """

    # ---------- NODE ----------
    pkg_file = repo / "package.json"
    if pkg_file.exists():
        framework = None
        try:
            pkg = pkg_file.read_text(errors="ignore").lower()

            if "next" in pkg:
                framework = "next"
            elif "nestjs" in pkg:
                framework = "nestjs"
            elif "express" in pkg:
                framework = "express"
            elif "react" in pkg:
                framework = "react"
            elif "vite" in pkg:
                framework = "vite"

        except Exception:
            pass

        return {"language": "node", "framework": framework}

    # ---------- PYTHON ----------
    if (repo / "requirements.txt").exists() or (repo / "pyproject.toml").exists():
        framework = None

        try:
            for f in safe_scan_python_files(repo):
                c = f.read_text(errors="ignore").lower()

                if "fastapi" in c:
                    framework = "fastapi"
                    break
                if "flask" in c:
                    framework = "flask"
                    break
                if "django" in c:
                    framework = "django"
                    break

        except Exception:
            pass

        return {"language": "python", "framework": framework}

    # ---------- JAVA ----------
    if (repo / "pom.xml").exists() or (repo / "build.gradle").exists():
        framework = None
        try:
            if (repo / "pom.xml").exists():
                pom = (repo / "pom.xml").read_text(errors="ignore").lower()
                if "spring-boot" in pom or "springframework" in pom:
                    framework = "spring"
        except Exception:
            pass

        return {"language": "java", "framework": framework}

    # ---------- GO ----------
    if (repo / "go.mod").exists():
        return {"language": "go", "framework": None}

    # ---------- RUST ----------
    if (repo / "Cargo.toml").exists():
        return {"language": "rust", "framework": None}

    # ---------- PHP ----------
    if (repo / "composer.json").exists():
        framework = None
        try:
            comp = (repo / "composer.json").read_text(errors="ignore").lower()
            if "laravel" in comp:
                framework = "laravel"
            elif "symfony" in comp:
                framework = "symfony"
        except Exception:
            pass

        return {"language": "php", "framework": framework}

    # ---------- .NET ----------
    if list(repo.glob("*.csproj")):
        return {"language": "dotnet", "framework": None}

    # ---------- FRONTEND STATIC ----------
    for depth in range(2):
        for html in repo.rglob("index.html"):
            if any(part in IGNORED_DIRS for part in html.parts):
                continue
            return {"language": "frontend-static", "framework": None}

    return {"language": "unknown", "framework": None}