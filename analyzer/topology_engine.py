"""
Architecture Topology Detector
================================
Given a list of classified services, determines the overall architecture pattern
and builds a communication dependency graph between services.

Topologies detected:
  single-service | two-tier | three-tier | monorepo | microservices
"""

from __future__ import annotations
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import re


# ---------------------------------------------------------------------------
# Communication Dependency Inference
# ---------------------------------------------------------------------------

class CommunicationMapper:
    """
    Infers which services talk to which, based on role patterns and
    environment variable / URL patterns in source.
    """

    # Env var patterns that hint at inter-service calls
    SERVICE_URL_ENV = re.compile(
        r'([\w_]+(?:_URL|_API|_SERVICE|_HOST|_ENDPOINT|_BASE_URL))\s*[=:]\s*["\'](http[^"\']+)["\']',
        re.IGNORECASE,
    )

    def infer_dependencies(
        self,
        services: List[dict],  # enriched service dicts with "classification"
    ) -> List[Dict]:
        """
        Returns a list of edges: {from, to, type, confidence}
        """
        edges = []
        role_map = {s["service"]: s["classification"]["role"] for s in services}

        for service in services:
            role = service["classification"]["role"]
            name = service["service"]

            # Pattern 1: frontend -> backend-api (universal truth)
            if role == "frontend":
                for svc, r in role_map.items():
                    if r == "backend-api" and svc != name:
                        edges.append({"from": name, "to": svc, "type": "http", "confidence": "high"})

            # Pattern 2: backend-api -> database (if DB used)
            if role == "backend-api":
                db_info = service.get("analysis", {}).get("database_used", {})
                if db_info.get("used"):
                    for svc, r in role_map.items():
                        if r == "database" and svc != name:
                            edges.append({"from": name, "to": svc, "type": "tcp", "confidence": "high"})
                    # Also mark external DB dependency
                    for db_type in db_info.get("types", []):
                        edges.append({"from": name, "to": f"external:{db_type}", "type": "tcp", "confidence": "medium"})

            # Pattern 3: gateway -> backend-api (gateway proxies to backends)
            if role == "gateway":
                for svc, r in role_map.items():
                    if r in {"backend-api", "ml-inference"} and svc != name:
                        edges.append({"from": name, "to": svc, "type": "http-proxy", "confidence": "high"})

            # Pattern 4: backend-api -> ml-inference (if both exist)
            if role == "backend-api":
                for svc, r in role_map.items():
                    if r == "ml-inference" and svc != name:
                        edges.append({"from": name, "to": svc, "type": "grpc-or-http", "confidence": "medium"})

            # Pattern 5: backend-api -> worker (event publishing)
            if role == "backend-api":
                for svc, r in role_map.items():
                    if r == "worker" and svc != name:
                        edges.append({"from": name, "to": svc, "type": "message-queue", "confidence": "medium"})

        # Deduplicate
        seen = set()
        unique_edges = []
        for e in edges:
            key = (e["from"], e["to"], e["type"])
            if key not in seen:
                seen.add(key)
                unique_edges.append(e)

        return unique_edges


# ---------------------------------------------------------------------------
# Architecture Topology Classifier
# ---------------------------------------------------------------------------

class ArchitectureDetector:
    """
    Determines overall architecture topology from the set of service roles.
    """

    def detect(self, services: List[dict]) -> str:
        """
        Args:
            services: enriched list with "classification" key

        Returns:
            topology string
        """
        if not services:
            return "unknown"

        roles = [s["classification"]["role"] for s in services]
        role_set = set(roles)
        service_count = len(services)

        # Single service
        if service_count == 1:
            return "single-service"

        # Microservices: many services, all with API/worker roles
        if service_count >= 4 and len(role_set) >= 3:
            return "microservices"

        # Monorepo: multiple services but same language / clearly grouped
        has_frontend = "frontend" in role_set
        has_backend = "backend-api" in role_set
        has_worker = "worker" in role_set
        has_ml = "ml-inference" in role_set
        has_gateway = "gateway" in role_set
        has_db = "database" in role_set

        # Three-tier: frontend + backend + (db or worker)
        if has_frontend and has_backend and (has_db or has_worker):
            return "three-tier"

        # Two-tier: frontend + backend  OR  backend + db
        if (has_frontend and has_backend) or (has_backend and has_db):
            return "two-tier"

        # Gateway present = likely microservices-lite or three-tier
        if has_gateway and service_count >= 3:
            return "microservices"

        # Multiple backends without frontend = monorepo or microservices
        if service_count >= 3:
            return "monorepo"

        return "two-tier"


# ---------------------------------------------------------------------------
# Topology Engine (main entry point)
# ---------------------------------------------------------------------------

class TopologyEngine:
    """
    Combines ArchitectureDetector + CommunicationMapper into one call.
    """

    def __init__(self):
        self._arch = ArchitectureDetector()
        self._comm = CommunicationMapper()

    def analyze(self, services: List[dict]) -> dict:
        """
        Args:
            services: list of enriched service dicts (with "classification" key)

        Returns:
            {
              "topology": str,
              "service_roles": dict,
              "communication_graph": list[dict],
              "tier_map": dict,
            }
        """
        topology = self._arch.detect(services)
        comm_graph = self._comm.infer_dependencies(services)
        role_map = {s["service"]: s["classification"]["role"] for s in services}
        tier_map = self._build_tier_map(services, topology)

        return {
            "topology": topology,
            "service_roles": role_map,
            "communication_graph": comm_graph,
            "tier_map": tier_map,
        }

    def _build_tier_map(self, services: List[dict], topology: str) -> dict:
        tier_map: Dict[str, List[str]] = {}

        TIER_NAMES = {
            "frontend": "presentation-tier",
            "gateway": "edge-tier",
            "backend-api": "application-tier",
            "ml-inference": "application-tier",
            "worker": "processing-tier",
            "database": "data-tier",
        }

        for s in services:
            role = s["classification"]["role"]
            tier = TIER_NAMES.get(role, "other")
            tier_map.setdefault(tier, []).append(s["service"])

        return tier_map