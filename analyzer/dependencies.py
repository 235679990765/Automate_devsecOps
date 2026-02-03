def detect_dependencies(repo, language):
    """
    Returns structured dependency info
    """

    files = []
    count = 0

    # ---------- FRONTEND STATIC ----------
    if language == "frontend-static":
        return {
            "declared": False,
            "files": [],
            "count": 0
        }

    # ---------- NODE ----------
    if language == "node" and (repo / "package.json").exists():
        files.append("package.json")
        if (repo / "package-lock.json").exists():
            files.append("package-lock.json")
        count = _count_lines(repo / "package.json")
        return {"declared": True, "files": files, "count": count}

    # ---------- PYTHON ----------
    if language == "python":
        if (repo / "requirements.txt").exists():
            files.append("requirements.txt")
            count = _count_lines(repo / "requirements.txt")
        if (repo / "pyproject.toml").exists():
            files.append("pyproject.toml")
            count += _count_lines(repo / "pyproject.toml")
        return {"declared": bool(files), "files": files, "count": count}

    # ---------- JAVA ----------
    if language == "java":
        if (repo / "pom.xml").exists():
            files.append("pom.xml")
        if (repo / "build.gradle").exists():
            files.append("build.gradle")
        return {"declared": bool(files), "files": files, "count": len(files)}

    # ---------- GO ----------
    if language == "go" and (repo / "go.mod").exists():
        return {
            "declared": True,
            "files": ["go.mod"],
            "count": _count_lines(repo / "go.mod")
        }

    # ---------- RUST ----------
    if language == "rust" and (repo / "Cargo.toml").exists():
        return {
            "declared": True,
            "files": ["Cargo.toml"],
            "count": _count_lines(repo / "Cargo.toml")
        }

    # ---------- PHP ----------
    if language == "php" and (repo / "composer.json").exists():
        return {
            "declared": True,
            "files": ["composer.json"],
            "count": _count_lines(repo / "composer.json")
        }

    # ---------- .NET ----------
    csproj = list(repo.glob("*.csproj"))
    if language == "dotnet" and csproj:
        return {
            "declared": True,
            "files": [f.name for f in csproj],
            "count": len(csproj)
        }

    return {
        "declared": False,
        "files": [],
        "count": 0
    }


def _count_lines(file):
    try:
        return len(file.read_text(errors="ignore").splitlines())
    except:
        return 0
