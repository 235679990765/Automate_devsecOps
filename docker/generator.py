from pathlib import Path
from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = Path(__file__).parent / "templates"
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

TEMPLATE_MAP = {
    "frontend-static": "frontend-static.Dockerfile.j2",
    "node": "node.Dockerfile.j2",
    "python": "python.Dockerfile.j2",
    "java": "java.Dockerfile.j2",
}


def generate_dockerfile(service_path: Path, analysis: dict):
    service_path.mkdir(parents=True, exist_ok=True)

    dockerfile_path = service_path / "Dockerfile"

    # Never overwrite
    if dockerfile_path.exists():
        return {"status": "skipped", "path": str(dockerfile_path)}

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
        raise RuntimeError(f"No Dockerfile template for {language}")

    # ------------------------------
    # Generate Dockerfile
    # ------------------------------
    template = env.get_template(TEMPLATE_MAP[language])

    dockerfile_path.write_text(
        template.render(
            port=analysis.get("runtime", {}).get("port"),
            health_endpoint=analysis.get("health_endpoint"),
        )
    )

    # ------------------------------
    # 🔥 AUTO-GENERATE nginx.conf
    # ------------------------------
    if language == "frontend-static":
        nginx_conf = service_path / "nginx.conf"

        if not nginx_conf.exists():
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

    return {
        "status": "generated",
        "language": language,
        "path": str(dockerfile_path),
    }
