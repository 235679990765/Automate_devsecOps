from pathlib import Path
from analyzer.repo_loader import load_repo
from analyzer.service_discovery import discover_services
from analyzer.analyzer_core import analyze_single_service

def analyze_repository(repo_input: str) -> dict:
    repo_path = Path(load_repo(repo_input))

    services = discover_services(repo_path)
    results = []

    for service in services:
        result = analyze_single_service(service["path"])
        results.append({
            "service": service["name"],
            "path": str(service["path"].relative_to(repo_path)),
            "deployable": service["deployable"],
            **result
        })

    return {
        "project_structure": "monorepo" if len(results) > 1 else "single-service",
        "services": results
    }
