import os
import sys
import getpass
from pathlib import Path

from analyzer.analyzer import analyze_repository
from analyzer.repo_loader import load_repo
from docker.generator import generate_dockerfile
from docker.builder import build_image
from docker.pusher import push_image
from docker.tagger import get_git_short_sha
from docker.auth import docker_login
from docker.runner import run_container
from docker.utils import sanitize_image_name   # ✅ NEW


def prompt_docker_credentials():
    print("\n🔐 Docker Hub login required to push images\n")
    username = input("Docker Hub Username: ").strip()
    token = getpass.getpass("Docker Hub Access Token: ").strip()

    if not username or not token:
        print("❌ Docker Hub credentials not provided")
        sys.exit(1)

    return username, token


def main():
    if len(sys.argv) < 3:
        print("Usage: python cli.py repo <repo-url>")
        sys.exit(1)

    if sys.argv[1] != "repo":
        print("Unknown command")
        sys.exit(1)

    repo_input = sys.argv[2]

    # 🔹 Load repo (workspace/UUID is CORRECT)
    repo_root = Path(load_repo(repo_input))

    # 🔹 Analyze
    print("\n🔍 Analyzing repository...\n")
    result = analyze_repository(repo_input)
    # print(result)
    # exit(0)

    # 🔹 Generate Dockerfiles
    print("\n🐳 Generating Dockerfiles...\n")
    for service in result["services"]:
        if service["deployable"]:
            generate_dockerfile(service, repo_root)

    # 🔐 Ask credentials AFTER dockerfiles
    docker_user, docker_token = prompt_docker_credentials()

    # 🔐 Docker login
    print("\n🔐 Logging into Docker Hub...\n")
    docker_login(docker_user, docker_token)

    # 🔹 Build, Push & Run
    # Better project name: repo name from URL (NOT UUID)
    project_raw = repo_input.rstrip("/").split("/")[-1].replace(".git", "")
    project = sanitize_image_name(project_raw)

    tag = get_git_short_sha(repo_root)

    print("\n🚀 Building, Pushing & Running Images...\n")

    for service in result["services"]:
        if not service["deployable"]:
            continue

        service_raw = service["service"]
        service_name = sanitize_image_name(service_raw)

        port = service["analysis"]["runtime"]["port"]

        image = f"{docker_user}/{project}-{service_name}:{tag}"

        build_image(repo_root, service, image)
        push_image(image)

        run_result = run_container(
            image=image,
            container_port=port,
            project=project,
            service_path=repo_root / service["path"],
            repo_root=repo_root,                # ✅ ADD THIS
            env_vars=service.get("env", {})
        )

        if run_result["status"] == "running":
            print(f"🌐 {service_name} running at → {run_result['url']}")

    print("\n🎉 DONE: Full automation successful\n")


if __name__ == "__main__":
    main()