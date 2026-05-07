from pathlib import Path

# ------------------------------------------------
# Core analyzer modules
# ------------------------------------------------
from analyzer.language import detect_language
from analyzer.dependencies import detect_dependencies
from analyzer.build import detect_build
from analyzer.runtime import detect_runtime
from analyzer.database import detect_database
from analyzer.health import detect_health
from analyzer.security.collector import collect_security_facts
from analyzer.mldetecore import detect_ml
from analyzer.dockerdetect import detect_dockerfiles
from analyzer.node_devdeps import analyze_node_dev_dependencies

# ------------------------------------------------
# Repo utilities
# ------------------------------------------------
from analyzer.repo_loader import load_repo
from analyzer.service_discovery import discover_services

# ------------------------------------------------
# Advanced intelligence engines
# ------------------------------------------------
from analyzer.service_classifier import ServiceClassifier
from analyzer.topology_engine import TopologyEngine
from analyzer.recommendation_engine import RecommendationEngine


# =========================================================
# Helpers
# =========================================================

def normalize_language(language_info):
    """
    Always returns a string language identifier
    """

    if isinstance(language_info, dict):
        return language_info.get("language")

    return language_info


# =========================================================
# Core Service Analyzer
# =========================================================

def analyze_single_service(repo: Path) -> dict:

    warnings = []
    confidence = 0

    # ------------------------------------------------
    # Language Detection
    # ------------------------------------------------
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

    if language != "unknown":
        confidence += 30
    else:
        warnings.append(
            "Unable to confidently detect project language"
        )

    # frontend-static confidence boost
    if language == "frontend-static":
        confidence += 40

    # normalize once
    language = normalize_language(language_info)

    # ------------------------------------------------
    # Dependency Analysis
    # ------------------------------------------------
    dependencies = detect_dependencies(repo, language)

    if isinstance(dependencies, dict):
        if dependencies.get("declared"):
            confidence += 30
        else:
            warnings.append("Dependency file missing")

    # ------------------------------------------------
    # Build Detection
    # ------------------------------------------------
    needs_build_step = detect_build(repo, language)

    confidence += 10

    # ------------------------------------------------
    # Runtime Detection
    # ------------------------------------------------
    runtime = detect_runtime(
        repo,
        language,
        framework
    )

    if runtime.get("start"):
        confidence += 20
    else:
        warnings.append(
            "Start command could not be determined"
        )

    if runtime.get("port"):
        confidence += 10
    else:
        warnings.append(
            "Application port could not be determined"
        )

    # ------------------------------------------------
    # Database Detection
    # ------------------------------------------------
    database_used = detect_database(repo)

    # ------------------------------------------------
    # Health Detection
    # ------------------------------------------------
    health_endpoint = detect_health(repo)

    if (
        language != "frontend-static"
        and health_endpoint is None
    ):
        warnings.append(
            "No health endpoint detected"
        )

    # ------------------------------------------------
    # Security Analysis
    # ------------------------------------------------
    security = collect_security_facts(
        repo,
        language
    )

    if security.get("risk_level") == "HIGH":
        warnings.append(
            "Potential hardcoded secrets detected"
        )
        confidence -= 20

    # ------------------------------------------------
    # Docker Detection
    # ------------------------------------------------
    dockerfile = detect_dockerfiles(repo)

    # ------------------------------------------------
    # ML Detection
    # ------------------------------------------------
    ml_detection = detect_ml(repo)

    # ------------------------------------------------
    # Node Dependency Analysis
    # ------------------------------------------------
    node_dependency_analysis = None

    if language == "node":
        node_dependency_analysis = (
            analyze_node_dev_dependencies(repo)
        )

    # ------------------------------------------------
    # Final Service Result
    # ------------------------------------------------
    return {

        "analysis": {

            "language": language_info,

            "dependencies": dependencies,

            "needs_build_step": needs_build_step,

            "runtime": runtime,

            "database_used": database_used,

            "health_endpoint": health_endpoint,

            "node_dependency_analysis":
                node_dependency_analysis
        },

        "confidence_score":
            max(min(confidence, 100), 0),

        "warnings": warnings,

        "security": security,

        "dockerfile": dockerfile,

        "ml_detection": ml_detection
    }


# =========================================================
# Repository Analyzer
# =========================================================

def analyze_repository(repo_input: str) -> dict:

    repo_path = Path(load_repo(repo_input))

    services = discover_services(repo_path)

    classifier = ServiceClassifier()

    topology_engine = TopologyEngine()

    recommender = RecommendationEngine()

    results = []

    languages = set()

    ml_services = []

    # ------------------------------------------------
    # Analyze each service
    # ------------------------------------------------
    for service in services:

        # --------------------------------------------
        # Core analyzer
        # --------------------------------------------
        result = analyze_single_service(
            service["path"]
        )

        enriched_service = {

            "service": service["name"],

            "path": str(
                service["path"].relative_to(repo_path)
            ),

            "deployable": service["deployable"],

            "analysis": result["analysis"],

            "confidence_score":
                result["confidence_score"],

            "warnings":
                result["warnings"],

            "security":
                result["security"],

            "dockerfile":
                result["dockerfile"],

            "ml_detection":
                result["ml_detection"]
        }

        # --------------------------------------------
        # Classification Engine
        # --------------------------------------------
        classification = classifier.classify(
            enriched_service,
            repo_path
        )

        enriched_service["classification"] = (
            classification
        )

        # --------------------------------------------
        # Repo-level intelligence
        # --------------------------------------------
        lang_info = result["analysis"]["language"]

        if isinstance(lang_info, dict):
            lang = lang_info.get("language")
        else:
            lang = lang_info

        if lang:
            languages.add(lang)

        if result["ml_detection"].get("enabled"):
            ml_services.append(
                service["name"]
            )

        results.append(enriched_service)

    # ------------------------------------------------
    # Topology Detection
    # ------------------------------------------------
    topology = topology_engine.analyze(
        results
    )

    # ------------------------------------------------
    # Recommendation Engine
    # ------------------------------------------------
    recommendations = recommender.generate(
        results,
        topology
    )

    # ------------------------------------------------
    # Final Repository Output
    # ------------------------------------------------
    return {

        "project_structure":
            topology["topology"],

        "repo_profile": {

            "total_services":
                len(results),

            "languages_used":
                list(languages),

            "polyglot":
                len(languages) > 1,

            "ml_services":
                ml_services
        },

        "topology":
            topology,

        "recommendations":
            recommendations,

        "services":
            results
    }