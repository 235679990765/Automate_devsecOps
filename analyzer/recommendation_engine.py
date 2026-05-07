"""
Deployment Recommendation Engine
=================================
Given the architecture topology and classified services, produces:
  - per-service deployment recommendations
  - kubernetes readiness assessment
  - CI/CD readiness assessment
  - integration flags for downstream generators
"""

from __future__ import annotations
from typing import List, Dict, Optional
import json


# ---------------------------------------------------------------------------
# Kubernetes Readiness Checker
# ---------------------------------------------------------------------------

class K8sReadinessChecker:
    """
    Evaluates each service for Kubernetes readiness and emits a structured
    report with recommendations.
    """

    def evaluate(self, service: dict) -> dict:
        issues = []
        recommendations = []
        score = 100  # start perfect, deduct

        analysis = service.get("analysis", {})
        classification = service.get("classification", {})
        role = classification.get("role", "unknown")
        security = service.get("security", {})
        runtime = analysis.get("runtime", {})
        dockerfile = service.get("dockerfile", {})
        deploy = classification.get("deployment_profile", {})

        # 1. Dockerfile
        if not dockerfile.get("exists"):
            issues.append("No Dockerfile present — will be auto-generated")
            score -= 5  # minor, we generate it

        # 2. Health check
        health = deploy.get("health_check_path") or analysis.get("health_endpoint")
        if role in {"backend-api", "gateway", "ml-inference"} and not health:
            issues.append("No health endpoint detected")
            recommendations.append("Add /health or /healthz endpoint returning HTTP 200")
            score -= 15

        # 3. Port definition
        if not runtime.get("port"):
            issues.append("Application port not detected")
            recommendations.append("Expose port explicitly via ENV or source code")
            score -= 10

        # 4. Secrets / security
        risk = security.get("risk_level", "LOW")
        if risk == "HIGH":
            issues.append("Potential hardcoded secrets found — Kubernetes Secrets required")
            recommendations.append("Move secrets to Kubernetes Secrets or external vault")
            score -= 20

        # 5. ML GPU resources
        resources = deploy.get("resources", {})
        if role == "ml-inference" and not resources.get("gpu"):
            recommendations.append("Consider GPU node selector for ML inference workloads")

        # 6. Persistent volume
        if deploy.get("needs_persistent_volume"):
            recommendations.append("Define PersistentVolumeClaim for stateful storage")

        # 7. Resource limits
        if not resources.get("cpu_limit"):
            issues.append("No resource limits defined")
            recommendations.append("Set CPU and memory limits in Kubernetes manifest")
            score -= 10

        ready = score >= 70
        level = "ready" if score >= 85 else "needs-work" if score >= 60 else "not-ready"

        return {
            "score": max(score, 0),
            "level": level,
            "ready": ready,
            "issues": issues,
            "recommendations": recommendations,
        }


# ---------------------------------------------------------------------------
# CI/CD Readiness Checker
# ---------------------------------------------------------------------------

class CICDReadinessChecker:
    """
    Evaluates each service for CI/CD pipeline generation readiness.
    """

    def evaluate(self, service: dict) -> dict:
        issues = []
        recommendations = []
        score = 100

        analysis = service.get("analysis", {})
        deps = analysis.get("dependencies", {})
        build = analysis.get("needs_build_step", {})
        security = service.get("security", {})
        dockerfile = service.get("dockerfile", {})
        classification = service.get("classification", {})
        role = classification.get("role", "unknown")

        # 1. Dependency file
        if not deps.get("declared"):
            issues.append("No dependency manifest found")
            recommendations.append("Add requirements.txt / package.json / pom.xml")
            score -= 20

        # 2. Build step
        if build.get("required") and not build.get("command"):
            issues.append("Build required but no command detected")
            score -= 15

        # 3. Tests
        # Simple heuristic: look for test dirs / test files  
        # (done via classification signals — if score exists use it)
        test_signal = self._has_tests(service)
        if not test_signal:
            recommendations.append("Add automated tests for CI pipeline integration")
            score -= 10

        # 4. Security scan capability
        if security.get("risk_level") in {"MEDIUM", "HIGH"}:
            recommendations.append("Integrate Trivy / Bandit / npm audit into CI pipeline")

        # 5. Docker
        if not dockerfile.get("exists"):
            recommendations.append("Dockerfile will be auto-generated — commit it to repo")

        stage_flags = {
            "lint": deps.get("declared", False),
            "test": test_signal,
            "build": build.get("required", False),
            "docker_build": True,
            "security_scan": True,  # always add
            "push": True,
            "deploy": role not in {"database"},
        }

        level = "ready" if score >= 80 else "partial" if score >= 50 else "incomplete"

        return {
            "score": max(score, 0),
            "level": level,
            "pipeline_stages": stage_flags,
            "issues": issues,
            "recommendations": recommendations,
        }

    def _has_tests(self, service: dict) -> bool:
        """Rough check for test presence via analysis metadata."""
        # No direct test detection in existing analyzer — use naming heuristics
        service_name = service.get("service", "").lower()
        return "test" not in service_name  # placeholder; real impl would scan dirs


# ---------------------------------------------------------------------------
# Per-Service Deployment Recommender
# ---------------------------------------------------------------------------

class DeploymentRecommender:
    """
    Generates per-service deployment recommendations combining all signals.
    """

    DOCKER_BASE_IMAGES = {
        ("python", "fastapi"): "python:3.11-slim",
        ("python", "flask"): "python:3.11-slim",
        ("python", "django"): "python:3.11-slim",
        ("python", None): "python:3.11-slim",
        ("node", "next"): "node:20-alpine",
        ("node", "nestjs"): "node:20-alpine",
        ("node", "express"): "node:20-alpine",
        ("node", None): "node:20-alpine",
        ("java", "spring"): "eclipse-temurin:21-jre-alpine",
        ("java", None): "eclipse-temurin:21-jre-alpine",
        ("go", None): "gcr.io/distroless/static-debian12",
        ("rust", None): "gcr.io/distroless/cc-debian12",
        ("frontend-static", None): "nginx:alpine",
    }

    def recommend(self, service: dict) -> dict:
        analysis = service.get("analysis", {})
        lang_info = analysis.get("language", {})
        language = lang_info.get("language", "unknown") if isinstance(lang_info, dict) else str(lang_info)
        framework = lang_info.get("framework") if isinstance(lang_info, dict) else None
        classification = service.get("classification", {})
        role = classification.get("role", "unknown")
        deploy = classification.get("deployment_profile", {})
        ml_det = service.get("ml_detection", {})

        base_image = (
            self.DOCKER_BASE_IMAGES.get((language, framework))
            or self.DOCKER_BASE_IMAGES.get((language, None))
            or "ubuntu:22.04"
        )

        k8s_manifest_type = self._k8s_kind(role)

        return {
            "docker": {
                "base_image": base_image,
                "multi_stage": analysis.get("needs_build_step", {}).get("required", False),
                "expose_port": analysis.get("runtime", {}).get("port", 8080),
            },
            "kubernetes": {
                "manifest_kind": k8s_manifest_type,
                "replicas": deploy.get("replicas", {"min": 1, "max": 3}),
                "resources": deploy.get("resources", {}),
                "expose_externally": deploy.get("expose_externally", False),
                "needs_pvc": deploy.get("needs_persistent_volume", False),
                "needs_gpu": ml_det.get("enabled", False),
                "service_type": "LoadBalancer" if deploy.get("expose_externally") else "ClusterIP",
                "ingress": deploy.get("expose_externally", False),
            },
            "cicd": {
                "build_tool": analysis.get("needs_build_step", {}).get("tool"),
                "build_command": analysis.get("needs_build_step", {}).get("command"),
                "test_required": role in {"backend-api", "ml-inference"},
                "security_scan": True,
                "push_registry": "docker-hub",
            },
            "scaling_strategy": self._scaling_strategy(role),
            "environment_vars_needed": self._env_vars(service),
        }

    def _k8s_kind(self, role: str) -> str:
        return {
            "database": "StatefulSet",
            "worker": "Deployment",
            "ml-inference": "Deployment",
            "backend-api": "Deployment",
            "frontend": "Deployment",
            "gateway": "Deployment",
        }.get(role, "Deployment")

    def _scaling_strategy(self, role: str) -> str:
        return {
            "frontend": "HPA (CPU-based)",
            "backend-api": "HPA (CPU + RPS)",
            "worker": "KEDA (queue-depth)",
            "ml-inference": "HPA (GPU utilization)",
            "gateway": "HPA (connection-count)",
            "database": "manual",
        }.get(role, "HPA (CPU-based)")

    def _env_vars(self, service: dict) -> List[str]:
        vars_ = ["ENV", "LOG_LEVEL"]
        db = service.get("analysis", {}).get("database_used", {})
        if db.get("used"):
            for t in db.get("types", []):
                vars_.append(f"{t.upper()}_URL")
        return vars_


# ---------------------------------------------------------------------------
# Main Recommendation Engine
# ---------------------------------------------------------------------------

class RecommendationEngine:
    """
    Combines K8s readiness, CI/CD readiness, and deployment recommendations
    for all services.
    """

    def __init__(self):
        self._k8s = K8sReadinessChecker()
        self._cicd = CICDReadinessChecker()
        self._deploy = DeploymentRecommender()

    def generate(self, services: List[dict], topology: dict) -> dict:
        """
        Args:
            services: enriched service dicts (must have "classification")
            topology: output from TopologyEngine.analyze()

        Returns:
            Full recommendations dict
        """
        service_recs = {}
        overall_k8s_score = 0
        overall_cicd_score = 0

        for svc in services:
            name = svc["service"]
            k8s = self._k8s.evaluate(svc)
            cicd = self._cicd.evaluate(svc)
            deploy = self._deploy.recommend(svc)

            service_recs[name] = {
                "kubernetes_readiness": k8s,
                "cicd_readiness": cicd,
                "deployment": deploy,
            }
            overall_k8s_score += k8s["score"]
            overall_cicd_score += cicd["score"]

        n = len(services) or 1

        return {
            "services": service_recs,
            "overall": {
                "kubernetes_readiness_score": round(overall_k8s_score / n),
                "cicd_readiness_score": round(overall_cicd_score / n),
                "architecture_topology": topology["topology"],
                "deployment_strategy": self._arch_strategy(topology["topology"]),
                "integration_flags": self._integration_flags(services, topology),
            },
        }

    def _arch_strategy(self, topology: str) -> str:
        return {
            "single-service": "single-deployment",
            "two-tier": "split-deployment",
            "three-tier": "layered-deployment",
            "monorepo": "independent-deployments",
            "microservices": "helm-umbrella-chart",
        }.get(topology, "single-deployment")

    def _integration_flags(self, services: List[dict], topology: dict) -> dict:
        roles = {s["classification"]["role"] for s in services}
        return {
            "dockerfile_generation": True,
            "cicd_pipeline_generation": True,
            "kubernetes_manifest_generation": True,
            "policy_as_code": any(
                s.get("security", {}).get("risk_level") in {"MEDIUM", "HIGH"}
                for s in services
            ),
            "security_scanning": True,
            "ml_pipeline": "ml-inference" in roles,
            "ingress_required": any(
                s["classification"]["deployment_profile"].get("expose_externally")
                for s in services
            ),
            "service_mesh_recommended": topology["topology"] == "microservices",
            "helm_chart_recommended": len(services) >= 3,
        }