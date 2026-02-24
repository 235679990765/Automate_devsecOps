# Automate DevSecOps

> A Python-based automation tool that analyzes application repositories, generates Dockerfiles, builds/pushes images, and runs containers for rapid DevSecOps workflows.

---

## 🚀 Overview

`Automate_devsecOps` is a CLI-driven toolkit designed to inspect arbitrary code repositories, determine language/framework/runtime metadata, detect security concerns, and automate the creation and deployment of containerized services. It provides:

- Language and framework detection (Python, Node, Java, Go, PHP, .NET, frontend-static, etc.)
- Dependency, build and runtime analysis
- Health endpoint and database detection
- Security fact collection and simple secret scanning
- Optional ML model detection
- Intelligent Dockerfile generation (with Jinja2 templates)
- Smart Docker image build with auto‑fix capabilities
- Automated container run/pull/build/reuse logic with environment variable support
- Project-wide service discovery and orchestration

This repository is intended for developers, security engineers, and DevOps teams who want a one‑command way to bootstrap containerized applications from source code.

---

## 🧩 Requirements

- **Python 3.11+** (any virtual environment manager is fine)
- **Docker CLI** (local engine must be running)
- Internet access for pulling base images and pushing to Docker Hub
- Optional: a Docker Hub account and access token

Install Python dependencies with:

```bash
pip install -r requirements.txt
```

> The `requirements.txt` contains packages such as `jinja2` used for template rendering.

---

## 🛠 Installation

1. Clone the repository:
   ```bash
git clone https://github.com/your-org/Automate_devsecOps.git
cd Automate_devsecOps
```
2. Create/activate a virtual environment and install dependencies.
3. Ensure Docker is installed and the daemon is running.

---

## 📁 Project Structure

```
cli.py                 # entry point for the command‑line tool
requirements.txt       # Python packages

analyzer/              # repository analysis logic
  analyzer_core.py     # orchestrates all detection steps
  analyzer.py          # high‑level service discovery
  build.py             # detect build steps (e.g. Maven, npm)
  dependencies.py      # dependency file presence and extra checks
  dockerdetect.py      # finds existing Dockerfiles
  health.py            # looks for health check endpoints
  language.py          # language/framework detection
  mldetecore.py        # simple ML inference or model detection
  node_devdeps.py      # deep analysis of package.json devDependencies
  repo_loader.py       # clones / downloads remote repo
  runtime.py           # figures out start commands and ports
  database.py          # checks for databases used (sqlalchemy, jdbc, etc.)
  security/            # security‑related collectors
    collector.py       # hardcoded secrets / risk scoring
    config.py          # security configuration
    dependencies.py    # (if any) dependency security hints
    secrets.py         # secret pattern scanning
  service_discovery.py # finds top‑level services within repo

docker/                # Docker‑related helpers
  auth.py              # login helper (Docker Hub)
  builder.py           # image build engine with auto‑fix
  generator.py         # Dockerfile templating / generation
  pusher.py            # push images to registry
  runner.py            # container run/pull/reuse logic
  tagger.py            # git SHA short tag generator
  utils.py             # image sanitization, pull helper, etc.
  env.py               # write `.env` files for containers
  templates/           # Jinja2 templates for various languages

utils/                 # small utility modules used across code
  config.py            # global constants or settings
  fs.py                # filesystem helpers

workspace/             # (empty) workspace for cloned repositories
```

> Many modules follow a simple `detect_*` naming pattern returning dictionaries of analysis details. See inline docstrings for more information.

---

## 📦 CLI Usage

The entry point is `cli.py`.

```bash
python cli.py repo <git-url|local-path>
```

### Workflow
1. **Load repository** – clones or validates the given path.
2. **Analyze** – runs language, dependency, runtime, health, database, security and ML detection on each service subdirectory.
3. **Generate Dockerfiles** – for every deployable service, a Dockerfile is created from a matched template (unless one already exists).
4. **Ask for Docker credentials** – prompts for Docker Hub username and access token before pushing images.
5. **Build** – smart build engine that can regenerate, auto‑fix base images, and fallback to generated Dockerfiles.
6. **Push** – tags images with `username/project-service:gitsha` and pushes to Docker Hub.
7. **Run** – containers are started locally, ports are managed, environment variables are injected, and previous containers may be reused.

Example output snippet:

```
🔍 Analyzing repository...
{'services': [...], 'warnings': [...], 'confidence': 85}

🐳 Generating Dockerfiles...
...generated frontend-static/Dockerfile

🔐 Docker Hub login required to push images
Docker Hub Username: aditya
Docker Hub Access Token: ****

✅ Logged in
🚀 Building, Pushing & Running Images...
🌐 service-a running at → http://localhost:30001
🎉 DONE: Full automation successful
```

> You may also run `python cli.py repo /path/to/local/checkout` to avoid cloning.

---

## 🔍 Analysis Components

### Language and Framework
`analyzer.language.detect_language()` looks for characteristic files like `package.json`, `requirements.txt`, `pom.xml`, etc. It additionally scans a small number of source files for framework keywords (FastAPI, Spring Boot, Laravel, etc.).

### Dependencies
`analyzer.dependencies.detect_dependencies()` checks for dependency manifests and reports whether they're present, missing, or only declared.

### Build Step
`analyzer.build.detect_build()` identifies common build tools (Maven, npm, pip, go build).

### Runtime
`analyzer.runtime.detect_runtime()` attempts to determine the start command and listening port by examining typical files (e.g. `Procfile`, `Dockerfile`, `setup.py`, `package.json` scripts) or using language conventions.

### Database & Health
`analyzer.database.detect_database()` and `analyzer.health.detect_health()` search source code for patterns indicating database usage or health endpoints.

### Security
`analyzer.security.collector.collect_security_facts()` aggregates results from scanners defined in `analyzer/security`. The default collector looks for hard‑coded passwords, API keys, and flags risk level.

### ML Detection
`analyzer.mldetecore.detect_ml()` inspects repositories for machine‑learning model artifacts or common libraries (like `tensorflow`, `torch`) to tag repos that may contain ML code.

### Dockerfile Detection
`analyzer.dockerdetect.detect_dockerfiles()` simply walks subdirectories looking for `Dockerfile` files, marking services as already containerized.

---

## 🐳 Docker Automation

The `docker` package provides the core container orchestration logic.

- `generator.py` uses Jinja2 templates found in `docker/templates` to render language‑specific Dockerfiles. It selects templates based on detected language, framework and build requirements.
- `builder.py` handles image builds, including:
  - Using existing `Dockerfile` if found
  - Auto‑fixing deprecated base images (e.g. `openjdk:11` → `eclipse-temurin:11-jre`)
  - Substituting a temporary multi‑stage build for broken Java Dockerfiles
  - Falling back to a freshly generated Dockerfile when necessary
- `pusher.py` wraps `docker push` with simple logging
- `runner.py` ensures the image exists (pulls or builds if needed), reuses existing containers, chooses free ports, writes `.env` files, and labels containers by project for cleanup.
- `auth.py` performs `docker login` using provided credentials.
- `tagger.py` generates a short git SHA tag for images.
- `env.py` writes environment variable files for a service from a dictionary.
- `utils.py` provides helpers like sanitizing image names and checking/pulling images from registries.

---

## 🧪 Testing & Development

This project currently does not ship with a formal test suite, but developers can exercise individual modules by importing them and calling detection functions against sample repositories. Logging is mostly done via `print()` statements for simplicity.

To extend functionality:
1. Add new detection functions under `analyzer/`.
2. Add or modify Jinja2 templates in `docker/templates`.
3. Update `generator.select_template()` logic for new language/framework combinations.
4. Enhance `builder.py` with additional auto‑fix rules.

> When editing Python code, run `flake8` or a similar linter as desired.

---

## 📄 License & Contribution

Specify your license here (e.g., MIT, Apache‑2.0) and contribution guidelines.

---

*Generated automatically by the project analysis engine.*
