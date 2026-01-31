from pathlib import Path
from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = Path(__file__).parent / "templates"
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

TEMPLATE_MAP = {
    "frontend-static": "frontend-static.Dockerfile.j2",
    "node": "node.Dockerfile.j2",
    "python": "python.Dockerfile.j2",
    "java": "java.Dockerfile.j2"
}


def generate_dockerfile(service_result: dict, repo_root: Path):
    service_path = repo_root / service_result["path"]
    service_path.mkdir(parents=True, exist_ok=True)

    dockerfile_path = service_path / "Dockerfile"

    # Rule: never overwrite existing Dockerfile
    if dockerfile_path.exists():
        return {
            "status": "skipped",
            "reason": "Dockerfile already exists",
            "path": str(dockerfile_path)
        }

    analysis = service_result["analysis"]

    # Normalize language
    language = analysis.get("language", "").strip().lower()

    if language not in TEMPLATE_MAP:
        return {
            "status": "skipped",
            "reason": f"No Dockerfile rules for language: {language}"
        }

    # Port is required for backend services
    port = analysis.get("runtime", {}).get("port")

    template = env.get_template(TEMPLATE_MAP[language])

    dockerfile_content = template.render(
        port=port,
        health_endpoint=analysis.get("health_endpoint")
    )

    dockerfile_path.write_text(dockerfile_content)

    # 🔥 NEW: Generate nginx.conf for frontend-static
    if language == "frontend-static":
        nginx_conf_path = service_path / "nginx.conf"

        if not nginx_conf_path.exists():
            nginx_template = env.get_template("nginx.conf.j2")
            nginx_conf_path.write_text(nginx_template.render())

    return {
        "status": "generated",
        "path": str(dockerfile_path)
    }
