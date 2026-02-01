from analyzer.scanner import iter_files

def detect_health(repo):
    for file in iter_files(repo):
        content = file.read_text(errors="ignore")
        if "/health" in content or "/healthz" in content:
            return "/health"
    return None
