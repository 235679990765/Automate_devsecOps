import json

def detect_build(repo, language):
    """
    Returns build metadata, not just True/False
    """

    # ---------- NODE ----------
    if language == "node" and (repo / "package.json").exists():
        pkg = json.load(open(repo / "package.json", errors="ignore"))
        scripts = pkg.get("scripts", {})

        if any(k in scripts for k in ["build", "compile", "prepare"]):
            return {
                "required": True,
                "tool": "npm",
                "command": "npm run build",
                "artifact": "dist/"
            }

        # runtime-only node app
        return {
            "required": False,
            "tool": None,
            "command": None,
            "artifact": None
        }

    # ---------- PYTHON ----------
    if language == "python":
        return {
            "required": False,
            "tool": None,
            "command": None,
            "artifact": None
        }

    # ---------- JAVA ----------
    if language == "java":
        if (repo / "pom.xml").exists():
            return {
                "required": True,
                "tool": "maven",
                "command": "mvn clean package",
                "artifact": "target/*.jar"
            }

        if (repo / "build.gradle").exists():
            return {
                "required": True,
                "tool": "gradle",
                "command": "gradle build",
                "artifact": "build/libs/*.jar"
            }

    # ---------- GO ----------
    if language == "go" and (repo / "go.mod").exists():
        return {
            "required": True,
            "tool": "go",
            "command": "go build -o app",
            "artifact": "app"
        }

    # ---------- RUST ----------
    if language == "rust" and (repo / "Cargo.toml").exists():
        return {
            "required": True,
            "tool": "cargo",
            "command": "cargo build --release",
            "artifact": "target/release/*"
        }

    # ---------- PHP ----------
    if language == "php":
        return {
            "required": False,
            "tool": "composer",
            "command": "composer install --no-dev",
            "artifact": None
        }

    # ---------- .NET ----------
    if language == "dotnet":
        return {
            "required": True,
            "tool": "dotnet",
            "command": "dotnet publish -c Release -o out",
            "artifact": "out/"
        }

    return {
        "required": False,
        "tool": None,
        "command": None,
        "artifact": None
    }
