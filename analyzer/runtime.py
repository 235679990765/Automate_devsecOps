import re

IGNORE_DIRS = {
    "node_modules",
    "test", "tests", "__tests__",
    "examples", "docs",
    ".github",
    "lib"
}

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
    start = _detect_start(language, framework)
    port, source = _detect_port(repo, language, framework)

    return {
        "start": start,
        "port": port,
        "port_detected_from": source
    }


def _detect_start(language, framework):
    # ✅ FastAPI special case
    if language == "python" and framework == "fastapi":
        return "uvicorn main:app --host 0.0.0.0 --port 8000"

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

    # 3️⃣ SOURCE CODE (FILTERED)
    for file in repo.rglob("*"):
        if file.suffix not in [".js", ".ts", ".py", ".go", ".rs", ".php", ".cs"]:
            continue

        if any(part in IGNORE_DIRS for part in file.parts):
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
