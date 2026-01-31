def detect_language(repo):
    # Backend first (always priority)
    if (repo / "package.json").exists():
        return "node"
    if (repo / "requirements.txt").exists() or (repo / "pyproject.toml").exists():
        return "python"
    if (repo / "pom.xml").exists() or (repo / "build.gradle").exists():
        return "java"

    # Frontend-static detection (root + 2 levels deep)
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

    return "unknown"
