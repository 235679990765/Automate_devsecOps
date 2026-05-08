from pathlib import Path

from generators.language_profiles import (
    LANGUAGE_PROFILES
)

from generators.framework_profiles import (
    FRAMEWORK_PROFILES
)


class GitHubActionsGenerator:

    # =====================================================
    # Generate Workflow File
    # =====================================================

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
            port=runtime.get("port", 80)
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

        # =================================================
        # Optional Build Step
        # =================================================

        if build:

            build_step = f"""
      - name: Build Application
        run: {build}
"""

        # =================================================
        # Optional Test Step
        # =================================================

        if test:

            test_step = f"""
      - name: Run Tests
        run: {test}
"""

        # =================================================
        # Final YAML
        # =================================================

        return f"""
name: Universal DevSecOps Pipeline

on:
  push:
    branches:
      - main

permissions:
  contents: read

jobs:

  # ===================================================
  # SECURITY SCAN
  # ===================================================

  security-scan:

    # ONLY run for generated automation commits
    if: contains(github.event.head_commit.message, 'Add generated DevSecOps automation')

    runs-on: ubuntu-latest

    steps:

      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Run Trivy Filesystem Scan
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: fs
          scan-ref: .

      - name: Run Semgrep Static Analysis
        uses: returntocorp/semgrep-action@v1

  # ===================================================
  # BUILD + PUSH CONTAINER
  # ===================================================

  build-and-push:

    if: contains(github.event.head_commit.message, 'Add generated DevSecOps automation')

    runs-on: ubuntu-latest

    needs: security-scan

    steps:

      - name: Checkout Repository
        uses: actions/checkout@v4

{setup}

{install}

{test_step}

{build_step}
      # ================================================
      # Debug Repository Files
      # ================================================

      - name: Debug Files
        run: |
          pwd
          ls -la
          cat Dockerfile || echo "Dockerfile missing"

      # ================================================
      # Verify Dockerfile Exists
      # ================================================

      - name: Verify Dockerfile
        run: |
          test -f Dockerfile

      # ================================================
      # Docker Login
      # ================================================

      - name: Docker Login
        run: |
          echo "${{{{ secrets.DOCKER_TOKEN }}}}" | docker login -u "${{{{ secrets.DOCKER_USERNAME }}}}" --password-stdin

      # ================================================
      # Build Docker Image
      # ================================================

      - name: Build Docker Image
        run: |
          docker build -t ${{{{ secrets.DOCKER_USERNAME }}}}/{service_name}:${{{{ github.sha }}}} .

      # ================================================
      # Push Docker Image
      # ================================================

      - name: Push Docker Image
        run: |
          docker push ${{{{ secrets.DOCKER_USERNAME }}}}/{service_name}:${{{{ github.sha }}}}

  # ===================================================
  # DEPLOY PLACEHOLDER
  # ===================================================

  deploy:

    if: contains(github.event.head_commit.message, 'Add generated DevSecOps automation')

    runs-on: ubuntu-latest

    needs: build-and-push

    steps:

      - name: Deployment Stage
        run: |
          echo "Continuous Deployment Running..."
          echo "Deployment completed successfully"

      - name: Service Information
        run: |
          echo "Service Name: {service_name}"
          echo "Language: {language}"
          echo "Framework: {framework}"
          echo "Port: {port}"
"""