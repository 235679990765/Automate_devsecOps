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
    "python": "python.Dockerfile.j2",
    "java": "java.Dockerfile.j2",
}


# -----------------------------------
# Dockerfile Generator
# -----------------------------------
def generate_dockerfile(service_path: Path, analysis: dict) -> dict:
    """
    Generates a Dockerfile (and nginx.conf if needed) for a service.

    Returns:
        {
            status: generated | skipped | error,
            language: <detected language>,
            path: <dockerfile path>,
            error: <optional error message>
        }
    """

    # ------------------------------
    # Validation
    # ------------------------------
    if not isinstance(service_path, Path):
        return {
            "status": "error",
            "error": f"service_path must be Path, got {type(service_path)}",
        }

    if not isinstance(analysis, dict):
        return {
            "status": "error",
            "error": f"analysis must be dict, got {type(analysis)}",
        }

    try:
        service_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to create service directory: {e}",
        }

    dockerfile_path = service_path / "Dockerfile"

    # ------------------------------
    # Never overwrite Dockerfile
    # ------------------------------
    if dockerfile_path.exists():
        return {
            "status": "skipped",
            "path": str(dockerfile_path),
        }

    # ------------------------------
    # SAFE language detection
    # ------------------------------
    raw_language = analysis.get("language")

    if isinstance(raw_language, dict):
        language = raw_language.get("name", "")
    elif isinstance(raw_language, str):
        language = raw_language
    else:
        language = ""

    language = language.lower().strip()

    # 🔥 Safe default
    if not language:
        language = "node"

    if language not in TEMPLATE_MAP:
        return {
            "status": "error",
            "language": language,
            "error": f"No Dockerfile template for language '{language}'",
        }

    # ------------------------------
    # Load template
    # ------------------------------
    try:
        template = env.get_template(TEMPLATE_MAP[language])
    except TemplateNotFound:
        return {
            "status": "error",
            "language": language,
            "error": f"Template file not found: {TEMPLATE_MAP[language]}",
        }

    # ------------------------------
    # Render Dockerfile
    # ------------------------------
    try:
        dockerfile_path.write_text(
            template.render(
                port=analysis.get("runtime", {}).get("port"),
                health_endpoint=analysis.get("health_endpoint"),
            )
        )
    except Exception as e:
        return {
            "status": "error",
            "language": language,
            "error": f"Failed to write Dockerfile: {e}",
        }

    # ------------------------------
    # AUTO-GENERATE nginx.conf
    # ------------------------------
    if language == "frontend-static":
        nginx_conf = service_path / "nginx.conf"

        if not nginx_conf.exists():
            try:
                nginx_conf.write_text(
                    """
server {
    listen 80;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri /index.html;
    }
}
""".strip()
                )
            except Exception as e:
                return {
                    "status": "error",
                    "language": language,
                    "error": f"Failed to write nginx.conf: {e}",
                }

    return {
        "status": "generated",
        "language": language,
        "path": str(dockerfile_path),
    }
