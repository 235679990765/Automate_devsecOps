from pathlib import Path

from generators.language_profiles import LANGUAGE_PROFILES
from generators.framework_profiles import FRAMEWORK_PROFILES


class GitHubActionsGenerator:

    def generate(
        self,
        analysis_result,
        output_dir
    ):

        workflow_dir = (
            Path(output_dir)
            / ".github"
            / "workflows"
        )

        workflow_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        workflow_file = (
            workflow_dir / "deploy.yml"
        )

        services = analysis_result["services"]

        service = services[0]

        runtime = (
            service["analysis"]["runtime"]
        )

        language_info = (
            service["analysis"]["language"]
        )

        language = language_info.get(
            "language"
        )

        framework = language_info.get(
            "framework"
        )

        yaml_content = self._generate_yaml(
            service_name=service["service"],
            language=language,
            framework=framework,
            port=runtime["port"]
        )

        workflow_file.write_text(
            yaml_content,
            encoding="utf-8"
        )

        return {
            "generated": True,
            "path": str(workflow_file)
        }

    # =====================================================
    # YAML Generator
    # =====================================================

    def _generate_yaml(
        self,
        service_name,
        language,
        framework,
        port
    ):

        language_profile = (
            LANGUAGE_PROFILES.get(
                language,
                {}
            )
        )

        framework_profile = (
            FRAMEWORK_PROFILES.get(
                framework,
                {}
            )
        )

        setup = language_profile.get(
            "setup",
            ""
        )

        install = language_profile.get(
            "install",
            ""
        )

        build = framework_profile.get(
            "build"
        )

        test = framework_profile.get(
            "test"
        )

        build_step = ""
        test_step = ""

        if build:
            build_step = f"""
      - name: Build Application
        run: {build}
"""

        if test:
            test_step = f"""
      - name: Run Tests
        run: {test}
"""

        return f"""
name: Universal DevSecOps Pipeline

on:
  push:
    branches:
      - main

jobs:

  security-scan:

    runs-on: ubuntu-latest

    steps:

      - name: Checkout
        uses: actions/checkout@v4

      - name: Run Trivy Scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: fs
          scan-ref: .

      - name: Run Semgrep
        uses: returntocorp/semgrep-action@v1

  build-and-push:

    runs-on: ubuntu-latest

    needs: security-scan

    steps:

      - name: Checkout
        uses: actions/checkout@v4

{setup}

{install}

{test_step}

{build_step}

      - name: Docker Login
        run: docker login -u ${{{{ secrets.DOCKER_USERNAME }}}} -p ${{{{ secrets.DOCKER_TOKEN }}}}

      - name: Build Docker Image
        run: |
          docker build -t {service_name}:${{{{ github.sha }}}} .

      - name: Push Docker Image
        run: |
          docker push {service_name}:${{{{ github.sha }}}}

  deploy:

    runs-on: ubuntu-latest

    needs: build-and-push

    steps:

      - name: Deploy Placeholder
        run: echo "Continuous Deployment Running..."
"""