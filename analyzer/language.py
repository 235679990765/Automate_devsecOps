def detect_language(repo):
    """
    Returns:
    {
      "language": str,
      "framework": str | None
    }
    """

    # ---------- NODE ----------
    if (repo / "package.json").exists():
        framework = None
        try:
            pkg = (repo / "package.json").read_text(errors="ignore").lower()
            if "express" in pkg:
                framework = "express"
            elif "next" in pkg:
                framework = "next"
        except:
            pass
        return {"language": "node", "framework": framework}

    # ---------- PYTHON ----------
    if (repo / "requirements.txt").exists() or (repo / "pyproject.toml").exists():
        framework = None
        try:
            for f in repo.rglob("*.py"):
                c = f.read_text(errors="ignore").lower()
                if "flask" in c:
                    framework = "flask"
                    break
                if "fastapi" in c:
                    framework = "fastapi"
                    break
        except:
            pass
        return {"language": "python", "framework": framework}

    # ---------- JAVA ----------
    if (repo / "pom.xml").exists() or (repo / "build.gradle").exists():
        framework = None
        try:
            if (repo / "pom.xml").exists():
                if "spring" in (repo / "pom.xml").read_text(errors="ignore").lower():
                    framework = "spring"
        except:
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
        except:
            pass
        return {"language": "php", "framework": framework}

    # ---------- .NET ----------
    for f in repo.glob("*.csproj"):
        return {"language": "dotnet", "framework": None}

    # ---------- FRONTEND STATIC ----------
    if (repo / "index.html").exists():
        return "frontend-static"
    
    for sub in repo.iterdir():
        if sub.is_dir():
            if (sub / "index.html").exists():
                return "frontend-static"

            # one more level deep (max depth = 2)
            for sub2 in sub.iterdir():
                if sub2.is_dir() and (sub2 / "index.html").exists():
                    return "frontend-static"

    return {"language": "unknown", "framework": None}
