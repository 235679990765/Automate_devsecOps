import re

DEFAULT_PORTS = {
    ("node", "express"): 3000,
    ("node", "next"): 3000,
    ("python", "flask"): 5000,
    ("python", "fastapi"): 8000,
    ("java", "spring"): 8080,
    ("go", None): 8080,
    ("rust", None): 8080,
    ("php", "laravel"): 8000,
    ("php", None): 80,
    ("dotnet", None): 8080,
    ("frontend-static", None): 80,
}


def detect_runtime(repo, language, framework):
    """
    Returns clean runtime data.
    NEVER returns tuples.
    """
    start = _detect_start(language)
    port, source = _detect_port(repo, language, framework)

    return {
        "start": start,
        "port": port,                      # ✅ ALWAYS int
        "port_detected_from": source       # ✅ metadata
    }


# ---------- START COMMAND ----------
def _detect_start(language):
    return {
        "frontend-static": "nginx -g 'daemon off;'",
        "node": "npm start",
        "python": "python main.py",
        "java": "java -jar app.jar",
        "go": "./app",
        "rust": "./app",
        "php": "php -S 0.0.0.0:8000 -t public",
        "dotnet": "dotnet app.dll"
    }.get(language)


# ---------- PORT DETECTION ----------
def _detect_port(repo, language, framework):
    # 1️⃣ ENV FILE
    for env in repo.rglob(".env"):
        for line in env.read_text(errors="ignore").splitlines():
            if line.startswith("PORT="):
                try:
                    return int(line.split("=")[1]), "env"
                except ValueError:
                    pass

    # 2️⃣ JAVA CONFIG
    for cfg in repo.rglob("*"):
        if cfg.name in ["application.properties", "application.yml"]:
            text = cfg.read_text(errors="ignore")
            m = re.search(r"server\.port\s*[:=]\s*(\d+)", text)
            if m:
                return int(m.group(1)), "config"

    # 3️⃣ SOURCE CODE
    for file in repo.rglob("*"):
        if file.suffix not in [".js", ".ts", ".py", ".go", ".rs", ".php", ".cs"]:
            continue

        text = file.read_text(errors="ignore")

        if language == "node":
            m = re.search(r"listen\((\d+)", text)
            if m:
                return int(m.group(1)), "source"

        if language == "python":
            m = re.search(r"port\s*=\s*(\d+)", text)
            if m:
                return int(m.group(1)), "source"

        if language in ["go", "rust"]:
            m = re.search(r":(\d{2,5})", text)
            if m:
                return int(m.group(1)), "source"

    # 4️⃣ DEFAULT
    return DEFAULT_PORTS.get((language, framework), 8080), "default"
