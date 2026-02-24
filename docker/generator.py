from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

# -----------------------------------
# Template setup
# -----------------------------------
TEMPLATE_DIR = Path(__file__).parent / "templates"

env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)

TEMPLATE_MAP = {
    "frontend-static": "frontend-static.Dockerfile.j2",
    "node": "node.Dockerfile.j2",
    "node-build": "node-build.Dockerfile.j2",
    "python": "python.Dockerfile.j2",
    "python-fastapi": "python-fastapi.Dockerfile.j2",
    "java": "java.Dockerfile.j2",
    "go": "go.Dockerfile.j2",
    "php": "php.Dockerfile.j2",
    "dotnet": "dotnet.Dockerfile.j2",
}


# -----------------------------------
# Template selection logic
# -----------------------------------
def select_template(analysis: dict) -> str:
    language_info = analysis.get("language", {})
    language = language_info.get("language")
    framework = language_info.get("framework")
    needs_build = analysis.get("needs_build_step", {}).get("required")

    if language == "node" and needs_build:
        return "node-build"

    if language == "python" and framework == "fastapi":
        return "python-fastapi"

    return language


# -----------------------------------
# Dockerfile Generator
# -----------------------------------
def generate_dockerfile(service_path: Path, analysis: dict) -> dict:
    if not isinstance(service_path, Path):
        return {"status": "error", "error": "service_path must be Path"}

    dockerfile_path = service_path / "Dockerfile"

    # Never overwrite
    if dockerfile_path.exists():
        return {
            "status": "skipped",
            "path": str(dockerfile_path),
        }

    template_key = select_template(analysis)

    if template_key not in TEMPLATE_MAP:
        return {
            "status": "error",
            "error": f"No Dockerfile template for {template_key}",
        }

    try:
        template = env.get_template(TEMPLATE_MAP[template_key])
    except TemplateNotFound:
        return {
            "status": "error",
            "error": f"Template file missing: {TEMPLATE_MAP[template_key]}",
        }

    try:
        # Check if pyproject.toml exists
        has_pyproject_toml = (service_path / "pyproject.toml").exists()
        
        dockerfile_path.write_text(
            template.render(
                port=analysis.get("runtime", {}).get("port"),
                health_endpoint=analysis.get("health_endpoint"),
                node_dependency_analysis=analysis.get("node_dependency_analysis"),
                has_pyproject_toml=has_pyproject_toml,
            )
        )
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to render Dockerfile: {e}",
        }

    # Auto nginx.conf for static
    if template_key == "frontend-static":
        nginx_conf = service_path / "nginx.conf"
        if not nginx_conf.exists():
            nginx_conf.write_text(
                """server {
    listen 80;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri /index.html;
    }
}"""
            )

    return {
        "status": "generated",
        "template": TEMPLATE_MAP[template_key],
        "path": str(dockerfile_path),
    }
