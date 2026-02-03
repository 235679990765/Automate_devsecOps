from pathlib import Path
from analyzer.language import detect_language
from analyzer.dependencies import detect_dependencies
from analyzer.build import detect_build
from analyzer.runtime import detect_runtime
from analyzer.database import detect_database
from analyzer.health import detect_health
from analyzer.security.collector import collect_security_facts
from analyzer.mldetecore import detect_ml
from analyzer.dockerdetect import detect_dockerfiles

def normalize_language(language_info):
    """
    Always returns a string language identifier
    """
    if isinstance(language_info, dict):
        return language_info.get("language")
    return language_info

def analyze_single_service(repo: Path) -> dict:
    warnings = []
    confidence = 0

    language_info = detect_language(repo)

    language = (
        language_info.get("language")
        if isinstance(language_info, dict)
        else language_info
    )

    framework = (
        language_info.get("framework")
        if isinstance(language_info, dict)
        else None
    )

    if language_info != "unknown":
        confidence += 30
    else:
        warnings.append("Unable to confidently detect project language")

    # frontend-static boost
    if language_info == "frontend-static":
        confidence += 40

    # 🔑 normalize once
    language = normalize_language(language_info)

    # ---------------- Dependencies ----------------
    dependencies = detect_dependencies(repo, language)

    if dependencies == "declared":
        confidence += 30
    elif dependencies == "missing":
        warnings.append("Dependency file missing")

    # ---------------- Build ----------------
    needs_build_step = detect_build(repo, language)
    confidence += 10

    # ---------------- Runtime ----------------
    runtime = detect_runtime(repo, language, framework)
    if runtime.get("start"):
        confidence += 20
    else:
        warnings.append("Start command could not be determined")

    if runtime.get("port"):
        confidence += 10
    else:
        warnings.append("Application port could not be determined")

    # ---------------- Extras ----------------
    database_used = detect_database(repo)
    health_endpoint = detect_health(repo)

    if language != "frontend-static" and health_endpoint is None:
        warnings.append("No health endpoint detected")

    # ---------------- Security ----------------
    security = collect_security_facts(repo, language)
    if security.get("risk_level") == "HIGH":
        warnings.append("Potential hardcoded secrets detected")
        confidence -= 20

    # ---------------- Docker & ML ----------------
    dockerfile = detect_dockerfiles(repo)
    ml_detection = detect_ml(repo)

    return {
        "analysis": {
            "language": language_info,   # keep metadata
            "dependencies": dependencies,
            "needs_build_step": needs_build_step,
            "runtime": runtime,
            "database_used": database_used,
            "health_endpoint": health_endpoint
        },
        "confidence_score": max(min(confidence, 100), 0),
        "warnings": warnings,
        "security": security,
        "dockerfile": dockerfile,
        "ml_detection": ml_detection
    }
