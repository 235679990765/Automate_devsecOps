"""
Service Classifier
==================
Classifies each detected service into a role:
  frontend | backend-api | database | worker | ml-inference | gateway

Uses a signal-scoring approach: multiple weak signals are combined into a
confident classification rather than a single keyword match.
"""

from __future__ import annotations
from pathlib import Path
import json
import re
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class ClassificationSignals:
    """Accumulates evidence for each possible service role."""
    frontend: int = 0
    backend_api: int = 0
    database: int = 0
    worker: int = 0
    ml_inference: int = 0
    gateway: int = 0

    def winner(self) -> str:
        scores = {
            "frontend": self.frontend,
            "backend-api": self.backend_api,
            "database": self.database,
            "worker": self.worker,
            "ml-inference": self.ml_inference,
            "gateway": self.gateway,
        }
        return max(scores, key=scores.get)

    def confidence(self) -> str:
        scores = sorted(
            [self.frontend, self.backend_api, self.database,
             self.worker, self.ml_inference, self.gateway],
            reverse=True
        )
        top, second = scores[0], scores[1] if len(scores) > 1 else 0
        if top == 0:
            return "low"
        gap = top - second
        if gap >= 4:
            return "high"
        if gap >= 2:
            return "medium"
        return "low"

    def as_dict(self) -> dict:
        return {
            "frontend": self.frontend,
            "backend-api": self.backend_api,
            "database": self.database,
            "worker": self.worker,
            "ml-inference": self.ml_inference,
            "gateway": self.gateway,
        }


# ---------------------------------------------------------------------------
# Signal Collectors
# ---------------------------------------------------------------------------

class _LanguageFrameworkSignals:
    """Score from language + framework alone."""

    FRONTEND_FRAMEWORKS = {"react", "next", "vite", "angular", "vue", "nuxt", "svelte", "gatsby", "remix"}
    BACKEND_FRAMEWORKS = {"express", "nestjs", "fastapi", "flask", "django", "spring", "laravel", "symfony"}
    GATEWAY_FRAMEWORKS = {"kong", "traefik", "nginx", "envoy", "haproxy"}
    ML_FRAMEWORKS = {"pytorch", "tensorflow", "sklearn", "keras", "onnx", "huggingface", "transformers", "diffusers", "lightgbm", "xgboost"}

    STATIC_LANGUAGES = {"frontend-static"}
    WORKER_LANGUAGES = set()  # Workers are usually same lang, but patterns differ

    def score(self, signals: ClassificationSignals, language: str, framework: Optional[str]):
        lang = (language or "").lower()
        fw = (framework or "").lower()

        # Static frontend
        if lang == "frontend-static":
            signals.frontend += 6

        # Framework-driven classification
        if fw in self.FRONTEND_FRAMEWORKS:
            signals.frontend += 5

        if fw in self.BACKEND_FRAMEWORKS:
            signals.backend_api += 5

        if fw in self.GATEWAY_FRAMEWORKS:
            signals.gateway += 6

        if fw in self.ML_FRAMEWORKS:
            signals.ml_inference += 5

        # Next.js is a full-stack framework – can be frontend OR backend-api
        if fw == "next":
            signals.backend_api += 2  # partial credit

        # NestJS = definitely backend API
        if fw == "nestjs":
            signals.backend_api += 2  # boost

        # FastAPI / Flask = backend API
        if fw in {"fastapi", "flask", "django"}:
            signals.backend_api += 3


class _FilePatternSignals:
    """Score from filenames, directory names, entry points."""

    FRONTEND_FILES = {
        "index.html", "app.tsx", "app.jsx", "app.vue",
        "main.tsx", "main.jsx", "vite.config.ts", "vite.config.js",
        "tailwind.config.js", "tailwind.config.ts",
        "next.config.js", "next.config.ts",
        "angular.json", "nuxt.config.ts",
    }
    BACKEND_FILES = {
        "main.py", "app.py", "server.py", "server.js", "server.ts",
        "app.js", "app.ts", "index.js", "index.ts",
        "manage.py", "wsgi.py", "asgi.py",
        "application.properties", "application.yml",
    }
    WORKER_FILES = {
        "worker.py", "worker.js", "worker.ts",
        "celery.py", "celeryconfig.py",
        "queue.py", "consumer.py", "producer.py",
        "tasks.py", "scheduler.py", "cron.py",
        "job.py", "jobs.py",
        "Procfile",  # usually has worker: or web: entries
    }
    ML_FILES = {
        "model.py", "train.py", "training.py", "inference.py",
        "predict.py", "predictor.py", "serve.py",
        "pipeline.py", "dataset.py", "dataloader.py",
        "model_server.py", "triton.py",
    }
    GATEWAY_FILES = {
        "nginx.conf", "nginx.conf.j2", "gateway.yaml",
        "kong.yaml", "traefik.yaml", "envoy.yaml",
        "proxy.conf", "haproxy.cfg",
    }
    ML_MODEL_EXTENSIONS = {".pkl", ".pt", ".pth", ".onnx", ".h5", ".pb", ".tflite", ".safetensors"}
    FRONTEND_DIRS = {"src", "public", "static", "assets", "pages", "components", "views", "styles"}
    BACKEND_DIRS = {"api", "routes", "controllers", "handlers", "services", "middleware", "models"}
    WORKER_DIRS = {"workers", "tasks", "jobs", "queues", "consumers"}
    ML_DIRS = {"models", "training", "inference", "ml", "ai", "notebooks", "experiments"}

    def score(self, signals: ClassificationSignals, repo: Path):
        all_files = set()
        all_dirs = set()

        for item in repo.rglob("*"):
            # Skip deep nested noise
            try:
                rel = item.relative_to(repo)
            except ValueError:
                continue
            parts = rel.parts
            if len(parts) > 5:
                continue
            if any(p in {"node_modules", ".git", "__pycache__", "venv", ".venv"} for p in parts):
                continue

            if item.is_file():
                all_files.add(item.name.lower())
                if item.suffix.lower() in self.ML_MODEL_EXTENSIONS:
                    signals.ml_inference += 3
            elif item.is_dir():
                all_dirs.add(item.name.lower())

        # Score by file matches
        signals.frontend += sum(2 for f in self.FRONTEND_FILES if f in all_files)
        signals.backend_api += sum(2 for f in self.BACKEND_FILES if f in all_files)
        signals.worker += sum(3 for f in self.WORKER_FILES if f in all_files)
        signals.ml_inference += sum(3 for f in self.ML_FILES if f in all_files)
        signals.gateway += sum(4 for f in self.GATEWAY_FILES if f in all_files)

        # Score by dir matches
        signals.frontend += sum(1 for d in self.FRONTEND_DIRS if d in all_dirs)
        signals.backend_api += sum(1 for d in self.BACKEND_DIRS if d in all_dirs)
        signals.worker += sum(2 for d in self.WORKER_DIRS if d in all_dirs)
        signals.ml_inference += sum(2 for d in self.ML_DIRS if d in all_dirs)


class _DependencySignals:
    """Score from package managers (requirements.txt, package.json, pom.xml etc)."""

    FRONTEND_PACKAGES = {
        "react", "react-dom", "next", "vue", "nuxt", "angular", "@angular/core",
        "svelte", "gatsby", "remix", "vite", "@vitejs/plugin-react",
        "webpack", "parcel", "tailwindcss", "styled-components",
    }
    BACKEND_PACKAGES = {
        "express", "fastapi", "flask", "django", "nestjs", "@nestjs/core",
        "spring-boot", "koa", "hapi", "restify", "fastify",
        "uvicorn", "gunicorn", "aiohttp",
    }
    WORKER_PACKAGES = {
        "celery", "rq", "dramatiq", "bull", "bullmq", "bee-queue",
        "rabbitmq", "pika", "kafka-python", "confluent-kafka",
        "apscheduler", "schedule", "node-cron", "agenda",
    }
    ML_PACKAGES = {
        "torch", "tensorflow", "keras", "sklearn", "scikit-learn",
        "transformers", "diffusers", "huggingface-hub", "onnxruntime",
        "lightgbm", "xgboost", "catboost", "pandas", "numpy",
        "triton", "ray", "mlflow", "wandb", "bentoml", "torchserve",
    }
    GATEWAY_PACKAGES = {
        "http-proxy", "http-proxy-middleware", "node-http-proxy",
        "express-gateway", "fastify-reply-from",
    }
    DATABASE_PACKAGES = {
        "psycopg2", "asyncpg", "pymysql", "mysqlclient",
        "pymongo", "motor", "redis", "aioredis",
        "sqlalchemy", "alembic", "typeorm", "sequelize", "prisma",
        "mongoose", "pg", "mysql2",
    }

    def score(self, signals: ClassificationSignals, repo: Path):
        text = self._collect_dep_text(repo)
        if not text:
            return

        text_lower = text.lower()

        for pkg in self.FRONTEND_PACKAGES:
            if pkg in text_lower:
                signals.frontend += 2

        for pkg in self.BACKEND_PACKAGES:
            if pkg in text_lower:
                signals.backend_api += 2

        for pkg in self.WORKER_PACKAGES:
            if pkg in text_lower:
                signals.worker += 3

        for pkg in self.ML_PACKAGES:
            if pkg in text_lower:
                signals.ml_inference += 3

        for pkg in self.GATEWAY_PACKAGES:
            if pkg in text_lower:
                signals.gateway += 3

        # Database deps alone don't classify, but workers + DB = worker pattern
        db_count = sum(1 for pkg in self.DATABASE_PACKAGES if pkg in text_lower)
        if db_count >= 2:
            signals.backend_api += 1  # DB-heavy = likely backend

    def _collect_dep_text(self, repo: Path) -> str:
        chunks = []
        for fname in ["package.json", "requirements.txt", "pyproject.toml",
                      "pom.xml", "build.gradle", "Cargo.toml", "composer.json"]:
            f = repo / fname
            if f.exists():
                try:
                    chunks.append(f.read_text(errors="ignore"))
                except Exception:
                    pass
        return "\n".join(chunks)


class _SourceCodeSignals:
    """Score from source code patterns (imports, route definitions, etc)."""

    # Max files to scan per repo
    MAX_FILES = 40

    IGNORED_DIRS = {"node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build"}

    ROUTE_PATTERNS = [
        re.compile(r"@app\.(get|post|put|delete|patch)\s*\("),    # Flask/FastAPI
        re.compile(r"router\.(get|post|put|delete|patch)\s*\("),  # Express
        re.compile(r"@(Get|Post|Put|Delete|Patch)\s*\("),          # NestJS
        re.compile(r"@(RequestMapping|GetMapping|PostMapping)"),    # Spring
    ]
    WORKER_PATTERNS = [
        re.compile(r"@celery\.task|@app\.task|\.delay\(|\.apply_async\("),
        re.compile(r"Queue\(\)|Bull\(|BullMQ|agenda\.define"),
        re.compile(r"kafka.*consumer|rabbitmq|pika\."),
        re.compile(r"while True:.*sleep|setInterval\(.*\d+000\)"),
    ]
    ML_PATTERNS = [
        re.compile(r"import torch|from torch|import tensorflow|import tf"),
        re.compile(r"model\.predict|model\.forward|model\.inference"),
        re.compile(r"load_model|from_pretrained|pipeline\("),
        re.compile(r"np\.array|pd\.DataFrame"),
    ]
    GATEWAY_PATTERNS = [
        re.compile(r"proxy_pass|upstream\s+\{|location\s+/"),       # nginx
        re.compile(r"createProxyMiddleware|http-proxy|proxy\.web"),  # node
        re.compile(r"httputil\.ReverseProxy|httputil\.NewSingleHostReverseProxy"),  # go
    ]

    def score(self, signals: ClassificationSignals, repo: Path):
        scanned = 0
        CODE_EXTS = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".conf"}

        for f in repo.rglob("*"):
            if scanned >= self.MAX_FILES:
                break
            if not f.is_file():
                continue
            if f.suffix not in CODE_EXTS:
                continue
            if any(p in self.IGNORED_DIRS for p in f.parts):
                continue

            try:
                text = f.read_text(errors="ignore")
            except Exception:
                continue

            scanned += 1

            for pattern in self.ROUTE_PATTERNS:
                if pattern.search(text):
                    signals.backend_api += 2
                    break

            for pattern in self.WORKER_PATTERNS:
                if pattern.search(text):
                    signals.worker += 3
                    break

            for pattern in self.ML_PATTERNS:
                if pattern.search(text):
                    signals.ml_inference += 2
                    break

            for pattern in self.GATEWAY_PATTERNS:
                if pattern.search(text):
                    signals.gateway += 3
                    break


class _NamingSignals:
    """Score from the service/directory name itself."""

    FRONTEND_KEYWORDS = {"frontend", "ui", "web", "client", "app", "portal", "dashboard", "spa"}
    BACKEND_KEYWORDS = {"backend", "api", "server", "service", "core", "rest", "graphql"}
    WORKER_KEYWORDS = {"worker", "task", "job", "queue", "scheduler", "cron", "consumer"}
    ML_KEYWORDS = {"ml", "ai", "model", "inference", "predict", "train", "nlp", "vision", "recommendation"}
    GATEWAY_KEYWORDS = {"gateway", "proxy", "ingress", "router", "lb", "nginx"}
    DATABASE_KEYWORDS = {"db", "database", "store", "storage", "cache", "redis", "mongo", "postgres"}

    def score(self, signals: ClassificationSignals, service_name: str):
        name = service_name.lower().replace("-", " ").replace("_", " ")
        words = set(name.split())

        if words & self.FRONTEND_KEYWORDS:
            signals.frontend += 3
        if words & self.BACKEND_KEYWORDS:
            signals.backend_api += 3
        if words & self.WORKER_KEYWORDS:
            signals.worker += 4
        if words & self.ML_KEYWORDS:
            signals.ml_inference += 4
        if words & self.GATEWAY_KEYWORDS:
            signals.gateway += 4
        if words & self.DATABASE_KEYWORDS:
            signals.database += 5


# ---------------------------------------------------------------------------
# Main Classifier
# ---------------------------------------------------------------------------

class ServiceClassifier:
    """
    Entry point. Given a service dict (from analyzer output) + repo path,
    returns a classification result dict.
    """

    def __init__(self):
        self._lang_fw = _LanguageFrameworkSignals()
        self._file_pat = _FilePatternSignals()
        self._deps = _DependencySignals()
        self._source = _SourceCodeSignals()
        self._naming = _NamingSignals()

    def classify(self, service: dict, repo_root: Path) -> dict:
        """
        Args:
            service: one entry from analyze_repository()["services"]
            repo_root: absolute Path to the cloned repo root

        Returns:
            {
              "role": str,
              "confidence": str,           # high | medium | low
              "signal_scores": dict,
              "runtime_type": str,
              "api_surface": dict,
              "deployment_profile": dict,
            }
        """
        signals = ClassificationSignals()

        analysis = service.get("analysis", {})
        lang_info = analysis.get("language", {})
        language = lang_info.get("language", "unknown") if isinstance(lang_info, dict) else str(lang_info)
        framework = lang_info.get("framework") if isinstance(lang_info, dict) else None

        service_name = service.get("service", "root")
        service_path_str = service.get("path", ".")
        service_path = (repo_root / service_path_str).resolve()

        # Run all signal collectors
        self._lang_fw.score(signals, language, framework)
        self._file_pat.score(signals, service_path)
        self._deps.score(signals, service_path)
        self._source.score(signals, service_path)
        self._naming.score(signals, service_name)

        # Special boost: ML detection from existing analyzer output
        ml_det = service.get("ml_detection", {})
        if ml_det.get("enabled"):
            signals.ml_inference += 4

        # Special boost: database packages with no API routes → pure worker/db
        db_info = analysis.get("database_used", {})
        if db_info.get("used") and signals.backend_api == 0 and signals.worker == 0:
            signals.database += 3

        role = signals.winner()
        confidence = signals.confidence()

        return {
            "role": role,
            "confidence": confidence,
            "signal_scores": signals.as_dict(),
            "runtime_type": self._classify_runtime(language, framework, role),
            "api_surface": self._detect_api_surface(service_path, language),
            "deployment_profile": self._deployment_profile(role, language, framework, analysis),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _classify_runtime(self, language: str, framework: Optional[str], role: str) -> str:
        """Coarse runtime classification."""
        if language == "frontend-static":
            return "static"
        if framework in {"next", "nuxt", "remix"}:
            return "ssr"
        if role == "worker":
            return "daemon"
        if role == "ml-inference":
            return "ml-server"
        if role == "gateway":
            return "proxy"
        if role in {"backend-api", "database"}:
            return "server"
        return "unknown"

    def _detect_api_surface(self, repo: Path, language: str) -> dict:
        """Sniff for API endpoints / schema files."""
        endpoints = []
        has_openapi = any([
            (repo / "openapi.yaml").exists(),
            (repo / "openapi.json").exists(),
            (repo / "swagger.yaml").exists(),
            (repo / "swagger.json").exists(),
            (repo / "api.yaml").exists(),
        ])

        # Try to extract basic routes from source
        ROUTE_RE = re.compile(
            r'(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            re.IGNORECASE,
        )
        scanned = 0
        CODE_EXTS = {".py", ".js", ".ts", ".jsx", ".tsx", ".java"}
        IGNORED = {"node_modules", ".git", "__pycache__", "venv", ".venv"}

        for f in repo.rglob("*"):
            if scanned >= 20:
                break
            if not f.is_file() or f.suffix not in CODE_EXTS:
                continue
            if any(p in IGNORED for p in f.parts):
                continue
            try:
                for m in ROUTE_RE.finditer(f.read_text(errors="ignore")):
                    endpoints.append(f"{m.group(1).upper()} {m.group(2)}")
                scanned += 1
            except Exception:
                pass

        return {
            "has_openapi_spec": has_openapi,
            "detected_endpoints": endpoints[:20],  # cap at 20
            "endpoint_count": len(endpoints),
        }

    def _deployment_profile(
        self,
        role: str,
        language: str,
        framework: Optional[str],
        analysis: dict,
    ) -> dict:
        runtime = analysis.get("runtime", {})
        build = analysis.get("needs_build_step", {})
        db = analysis.get("database_used", {})

        replicas_min, replicas_max = self._replica_hints(role)
        resources = self._resource_hints(role, framework)

        return {
            "replicas": {"min": replicas_min, "max": replicas_max},
            "resources": resources,
            "needs_persistent_volume": db.get("used", False) or role == "database",
            "needs_service_account": role in {"gateway", "ml-inference"},
            "expose_externally": role in {"frontend", "backend-api", "gateway"},
            "health_check_path": analysis.get("health_endpoint") or self._default_health(role),
            "startup_probe_needed": role in {"ml-inference", "backend-api"},
        }

    def _replica_hints(self, role: str):
        return {
            "frontend": (2, 10),
            "backend-api": (2, 20),
            "gateway": (2, 5),
            "worker": (1, 10),
            "ml-inference": (1, 5),
            "database": (1, 1),
        }.get(role, (1, 3))

    def _resource_hints(self, role: str, framework: Optional[str]) -> dict:
        if role == "ml-inference":
            return {"cpu_request": "500m", "cpu_limit": "4", "memory_request": "2Gi", "memory_limit": "8Gi", "gpu": True}
        if role in {"backend-api", "gateway"}:
            return {"cpu_request": "250m", "cpu_limit": "2", "memory_request": "256Mi", "memory_limit": "2Gi", "gpu": False}
        if role == "worker":
            return {"cpu_request": "100m", "cpu_limit": "1", "memory_request": "128Mi", "memory_limit": "1Gi", "gpu": False}
        if role == "frontend":
            return {"cpu_request": "50m", "cpu_limit": "500m", "memory_request": "64Mi", "memory_limit": "256Mi", "gpu": False}
        return {"cpu_request": "100m", "cpu_limit": "1", "memory_request": "128Mi", "memory_limit": "512Mi", "gpu": False}

    def _default_health(self, role: str) -> Optional[str]:
        return {
            "backend-api": "/health",
            "gateway": "/healthz",
            "ml-inference": "/health",
            "frontend": None,
            "worker": None,
            "database": None,
        }.get(role)