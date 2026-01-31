import re
from analyzer.scanner import iter_files

SECRET_PATTERNS = {
    "AWS_ACCESS_KEY": r"AKIA[0-9A-Z]{16}",
    "JWT": r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
    "PASSWORD": r"password\s*=\s*['\"].+['\"]",
    "API_KEY": r"api[_-]?key\s*=\s*['\"].+['\"]"
}

def scan_secrets(repo):
    findings = []

    for file in iter_files(repo):
        content = file.read_text(errors="ignore")
        for name, pattern in SECRET_PATTERNS.items():
            if re.search(pattern, content, re.IGNORECASE):
                findings.append({
                    "type": name,
                    "file": str(file)
                })

    return findings
