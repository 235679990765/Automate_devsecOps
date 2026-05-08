import os
import sys
import getpass

from pathlib import Path
from kubernetes.generator import (
    KubernetesGenerator
)

from analyzer.analyzer import (
    analyze_repository
)

from analyzer.repo_loader import (
    load_repo
)

from docker.generator import (
    generate_dockerfile
)

from docker.builder import (
    build_image
)

from docker.pusher import (
    push_image
)

from docker.tagger import (
    get_git_short_sha
)

from docker.auth import (
    docker_login
)

from docker.runner import (
    run_container
)

from docker.utils import (
    sanitize_image_name
)

from generators.github_actions import (
    GitHubActionsGenerator
)

from security.scanner import (
    SecurityScanner
)


# =====================================================
# Docker Credentials Prompt
# =====================================================

def prompt_docker_credentials():

    print(
        "\n🔐 Docker Hub login required\n"
    )

    username = input(
        "Docker Hub Username: "
    ).strip()

    token = getpass.getpass(
        "Docker Hub Access Token: "
    ).strip()

    if not username or not token:

        print(
            "❌ Docker credentials missing"
        )

        sys.exit(1)

    return username, token


# =====================================================
# Main CLI
# =====================================================

def main():

    # =================================================
    # Validate CLI args
    # =================================================

    if len(sys.argv) < 3:

        print(
            "Usage:\n"
            "python cli.py repo <repo-url>"
        )

        sys.exit(1)

    if sys.argv[1] != "repo":

        print("❌ Unknown command")

        sys.exit(1)

    repo_input = sys.argv[2]

    # =================================================
    # Load Repository
    # =================================================

    print(
        "\n📥 Loading repository...\n"
    )

    repo_root = Path(
        load_repo(repo_input)
    )

    print(
        f"✅ Repository loaded:\n"
        f"{repo_root}"
    )

    # =================================================
    # Analyze Repository
    # =================================================

    print(
        "\n🔍 Analyzing repository...\n"
    )

    result = analyze_repository(
        repo_input
    )

    print(
        "\n✅ Analysis completed\n"
    )

    print(result)

    # =================================================
    # Generate GitHub Actions Pipeline
    # =================================================

    print(
        "\n⚙️ Generating CI/CD Pipeline...\n"
    )

    pipeline_generator = (
        GitHubActionsGenerator()
    )

    pipeline_result = (
        pipeline_generator.generate(
            analysis_result=result,
            output_dir=repo_root
        )
    )

    print(
        f"✅ GitHub Actions workflow generated:\n"
        f"{pipeline_result['path']}"
    )

    # =================================================
    # Generate Dockerfiles
    # =================================================

    print(
        "\n🐳 Generating Dockerfiles...\n"
    )

    for service in result["services"]:

        if not service["deployable"]:
            continue

        try:

            service_path = (
                repo_root / service["path"]
            )

            docker_result = (
                generate_dockerfile(
                    service_path=service_path,
                    analysis=service["analysis"]
                )
            )

            print(docker_result)

            if (
                docker_result["status"]
                == "generated"
            ):

                print(
                    f"✅ Dockerfile generated "
                    f"for: {service['service']}"
                )

            elif (
                docker_result["status"]
                == "skipped"
            ):

                print(
                    f"⚠️ Dockerfile already exists "
                    f"for: {service['service']}"
                )

            else:

                print(
                    f"❌ Docker generation failed "
                    f"for: {service['service']}"
                )

        except Exception as docker_error:

            print(
                f"⚠️ Docker generation failed:\n"
                f"{docker_error}"
            )

    print(
        "\n✅ Docker generation stage complete"
    )

    # =================================================
    # Security Scan
    # =================================================

    print(
        "\n🛡 Running Security Scan...\n"
    )

    scanner = SecurityScanner()

    security_report = scanner.scan(
        repo_root
    )

    print(
        "\n📋 Security Report:\n"
    )

    print(security_report)

    # Save JSON report
    scanner.logger.save_json(
        "security_report.json"
    )

    print(
        "\n✅ Security report saved:"
        "\nsecurity_report.json"
    )

    # =================================================
    # Docker Login
    # =================================================

    docker_user, docker_token = (
        prompt_docker_credentials()
    )

    print(
        "\n🔐 Logging into Docker Hub...\n"
    )

    docker_login(
        docker_user,
        docker_token
    )

    # =================================================
    # Build + Push + Run
    # =================================================

    project_raw = (
        repo_input
        .rstrip("/")
        .split("/")[-1]
        .replace(".git", "")
    )

    project = sanitize_image_name(
        project_raw
    )

    tag = get_git_short_sha(
        repo_root
    )

    print(
        "\n🚀 Building, Pushing & Running Images...\n"
    )

    for service in result["services"]:

        if not service["deployable"]:
            continue

        service_raw = service["service"]

        service_name = sanitize_image_name(
            service_raw
        )

        runtime = (
            service["analysis"]["runtime"]
        )

        port = runtime.get(
            "port",
            80
        )

        image = (
            f"{docker_user}/"
            f"{project}-"
            f"{service_name}:"
            f"{tag}"
        )

        print(
            f"\n🐳 Processing service:"
            f"\n{service_name}"
        )

        # =============================================
        # Docker Build
        # =============================================

        build_image(
            repo_root,
            service,
            image
        )

        print(
            f"✅ Docker image built:\n"
            f"{image}"
        )

        # =============================================
        # Docker Push
        # =============================================

        push_image(image)

        print(
            f"✅ Docker image pushed:\n"
            f"{image}"
        )

        # =============================================
        # Run Container
        # =============================================

        run_result = run_container(
            image=image,
            container_port=port,
            project=project,
            service_path=(
                repo_root
                / service["path"]
            ),
            repo_root=repo_root,
            env_vars=service.get(
                "env",
                {}
            )
        )

        if (
            run_result["status"]
            == "running"
        ):

            print(
                f"🌐 Service running:\n"
                f"{run_result['url']}"
            )

        else:

            print(
                f"❌ Failed to run service:"
                f"\n{service_name}"
            )

    # =================================================
    # Completed
    # =================================================

    print(
        "\n🎉 FULL DEVSECOPS AUTOMATION COMPLETED\n"
    )


# =====================================================
# Entry Point
# =====================================================

if __name__ == "__main__":

    main()