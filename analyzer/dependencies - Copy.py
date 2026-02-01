def detect_dependencies(repo, language):
    if language == "frontend-static":
        return "not_required"

    if language == "python":
        return "declared" if (
            (repo / "requirements.txt").exists() or
            (repo / "pyproject.toml").exists()
        ) else "missing"

    if language == "node":
        return "declared" if (repo / "package.json").exists() else "missing"

    if language == "java":
        return "declared" if (
            (repo / "pom.xml").exists() or
            (repo / "build.gradle").exists()
        ) else "missing"

    return "unknown"
