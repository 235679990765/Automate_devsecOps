from pathlib import Path
from analyzer.language import detect_language
from analyzer.dependencies import detect_dependencies
from analyzer.build import detect_build
from analyzer.runtime import detect_runtime
from analyzer.database import detect_database
from analyzer.health import detect_health
from analyzer.security.collector import collect_security_facts

def analyze_single_service(repo: Path) -> dict:
    warnings = []
    confidence = 0

    language = detect_language(repo)
    if language != "unknown":
        confidence += 30
    else:
        warnings.append("Unable to confidently detect project language")

    if language == "frontend-static":
        confidence += 40

    dependencies = detect_dependencies(repo, language)
    if dependencies == "declared":
        confidence += 30
    elif dependencies == "missing":
        warnings.append("Dependency file missing")

    needs_build_step = detect_build(repo, language)
    confidence += 10

    runtime = detect_runtime(language)
    if runtime["start"]:
        confidence += 20
    else:
        warnings.append("Start command could not be determined")

    if runtime["port"]:
        confidence += 10
    else:
        warnings.append("Application port could not be determined")

    database_used = detect_database(repo)
    health_endpoint = detect_health(repo)

    if language != "frontend-static" and health_endpoint is None:
        warnings.append("No health endpoint detected")

    security = collect_security_facts(repo, language)
    if security["risk_level"] == "HIGH":
        warnings.append("Potential hardcoded secrets detected")
        confidence -= 20

    dockerfile_exists = (repo / "Dockerfile").exists()

    return {
        "analysis": {
            "language": language,
            "dependencies": dependencies,
            "needs_build_step": needs_build_step,
            "runtime": runtime,
            "database_used": database_used,
            "health_endpoint": health_endpoint
        },
        "confidence_score": max(min(confidence, 100), 0),
        "warnings": warnings,
        "security": security,
        "dockerfile": {
            "exists": dockerfile_exists,
            "path": "Dockerfile" if dockerfile_exists else None
        }
    }
