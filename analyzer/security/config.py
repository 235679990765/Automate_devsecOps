from analyzer.scanner import iter_files

INSECURE_CONFIGS = [
    "debug=true",
    "allowAllOrigins=true",
    "disableAuth=true"
]

def scan_config(repo):
    findings = []

    for file in iter_files(repo):
        content = file.read_text(errors="ignore").lower()
        for flag in INSECURE_CONFIGS:
            if flag.lower() in content:
                findings.append({
                    "flag": flag,
                    "file": str(file)
                })

    return findings
