from analyzer.scanner import iter_files

INSECURE_LIBS = {
    "node": ["event-stream", "request"],
    "python": ["pickle", "yaml.load"],
    "java": ["commons-collections"]
}

def scan_dependency_risks(repo, language):
    findings = []

    for file in iter_files(repo):
        content = file.read_text(errors="ignore").lower()

        for lib in INSECURE_LIBS.get(language, []):
            if lib in content:
                findings.append({
                    "library": lib,
                    "file": str(file)
                })

    return findings
