import subprocess
from pathlib import Path
from docker.generator import generate_dockerfile


def image_exists(image: str) -> bool:
    """Check if image exists"""
    try:
        subprocess.check_output(
            ["docker", "inspect", image],
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False


def remove_image(image: str):
    """Remove image forcefully"""
    try:
        subprocess.run(
            ["docker", "rmi", "-f", image],
            check=False,
            capture_output=True
        )
    except subprocess.CalledProcessError:
        pass


def build_image(repo_root: Path, service: dict, image: str):
    """
    Intelligent Docker build engine.

    Behavior:
    1. If Dockerfile exists → try build
    2. If single-stage Java with missing target → convert to multi-stage
    3. If deprecated base → auto-fix
    4. If still failing → fallback to generated Dockerfile
    """

    service_path = repo_root / service["path"]
    dockerfile_path = service_path / "Dockerfile"
    analysis = service.get("analysis", {})

    # --------------------------------------------------
    # STEP 1: Ensure Dockerfile exists
    # --------------------------------------------------
    if not dockerfile_path.exists():
        print("🐳 No Dockerfile found. Generating new one...")
        result = generate_dockerfile(
            service_path=service_path,
            analysis=analysis
        )
        if result.get("status") == "error":
            raise RuntimeError(result.get("error"))

    if not dockerfile_path.exists():
        raise RuntimeError("Dockerfile missing and generation failed.")

    print("🐳 Using existing Dockerfile")

    # --------------------------------------------------
    # STEP 2: Detect broken single-stage Java Dockerfile
    # --------------------------------------------------
    df_text = dockerfile_path.read_text()
    df_lower = df_text.lower()

    needs_build = analysis.get("needs_build_step", {}).get("required")
    is_java = analysis.get("language", {}).get("language") == "java"
    target_exists = (service_path / "target").exists()

    if (
        is_java
        and needs_build
        and "add target" in df_lower
        and not target_exists
    ):
        print("⚠️ Broken single-stage Java Dockerfile detected.")
        print("🔄 Will attempt safe multi-stage build without overwriting repository Dockerfile...")
        # keep original content intact; we'll try temp Dockerfiles later if needed

    # --------------------------------------------------
    # STEP 3: Attempt Normal Build
    # --------------------------------------------------
    build_cmd = [
        "docker", "build",
        "-t", image,
        "-f", str(dockerfile_path),
        str(service_path),
    ]

    try:
        subprocess.run(build_cmd, check=True)
        return {"status": "built", "image": image}

    except subprocess.CalledProcessError:
        print("❌ Initial build failed.")
        print("🔧 Attempting base image auto-fix...")

    # --------------------------------------------------
    # STEP 4: Base Image Auto-Fix
    # --------------------------------------------------
    replacements = {
        "openjdk:8": "eclipse-temurin:8-jre",
        "openjdk:11": "eclipse-temurin:11-jre",
        "openjdk:17": "eclipse-temurin:17-jre",
        "node:10": "node:18-alpine",
        "node:12": "node:18-alpine",
        "python:2.7": "python:3.11-slim",
        "ubuntu:16.04": "ubuntu:22.04",
    }

    patched = df_text
    replaced = False

    for old, new in replacements.items():
        if old in patched.lower():
            print(f"🔁 Replacing {old} → {new}")
            patched = patched.replace(old, new)
            replaced = True

    if replaced:
        temp_dockerfile = service_path / "Dockerfile.autofix"
        temp_dockerfile.write_text(patched)

        try:
            subprocess.run(
                [
                    "docker", "build",
                    "-t", image,
                    "-f", str(temp_dockerfile),
                    str(service_path),
                ],
                check=True
            )
            print("✅ Build succeeded after auto-fix")
            temp_dockerfile.unlink(missing_ok=True)
            return {"status": "built_with_autofix", "image": image}

        except subprocess.CalledProcessError:
            print("❌ Auto-fix build failed.")
            temp_dockerfile.unlink(missing_ok=True)

    # --------------------------------------------------
    # STEP 5: Final Fallback → Fresh Generated Dockerfile
    # --------------------------------------------------
    print("⚠️ Falling back to safer options...")

    # If Java project with build step, try a temporary multi-stage Dockerfile (don't overwrite repo file)
    if is_java and needs_build:
        java_ver = None
        pom = service_path / "pom.xml"
        try:
            pom_text = pom.read_text() if pom.exists() else ""
            if "<java.version>1.8</java.version>" in pom_text or "<java.version>8" in pom_text or "<source>1.8</source>" in pom_text:
                java_ver = "8"
        except Exception:
            java_ver = None

        if java_ver == "8":
            build_stage = (
                "FROM maven:3.6.3-jdk-8 AS build\n"
                "WORKDIR /app\n\n"
                "COPY pom.xml ./\n"
                "RUN mvn dependency:go-offline -q\n\n"
                "COPY src ./src\n"
                "RUN mvn clean package -DskipTests -q\n\n"
                "FROM eclipse-temurin:8-jre\n"
                "WORKDIR /app\n\n"
                "COPY --from=build /app/target/*.jar app.jar\n\n"
                "RUN groupadd -r app && useradd -r -g app app\n"
                "USER app\n\n"
                f"EXPOSE {analysis.get('runtime', {}).get('port', 8080)}\n\n"
                "CMD [\"java\", \"-jar\", \"app.jar\"]"
            )
        else:
            build_stage = (
                "FROM maven:3.9-eclipse-temurin-11 AS build\n"
                "WORKDIR /app\n\n"
                "COPY pom.xml ./\n"
                "RUN mvn dependency:go-offline -q\n\n"
                "COPY src ./src\n"
                "RUN mvn clean package -DskipTests -q\n\n"
                "FROM eclipse-temurin:11-jre-alpine\n"
                "WORKDIR /app\n\n"
                "COPY --from=build /app/target/*.jar app.jar\n\n"
                "RUN addgroup -S app && adduser -S app -G app\n"
                "USER app\n\n"
                f"EXPOSE {analysis.get('runtime', {}).get('port', 8080)}\n\n"
                "CMD [\"java\", \"-jar\", \"app.jar\"]"
            )

        temp_dockerfile = service_path / "Dockerfile.autofix"
        temp_dockerfile.write_text(build_stage)

        try:
            subprocess.run([
                "docker", "build",
                "-t", image,
                "-f", str(temp_dockerfile),
                str(service_path),
            ], check=True)
            temp_dockerfile.unlink(missing_ok=True)
            return {"status": "built_with_autofix_multistage", "image": image}
        except subprocess.CalledProcessError:
            temp_dockerfile.unlink(missing_ok=True)

    # Final fallback: generate Dockerfile from templates (will write to repo Dockerfile)
    result = generate_dockerfile(
        service_path=service_path,
        analysis=analysis
    )

    if result.get("status") == "error":
        raise RuntimeError(result.get("error"))

    try:
        subprocess.run([
            "docker", "build",
            "-t", image,
            str(service_path),
        ], check=True)
        return {"status": "built_with_generated", "image": image}
    except subprocess.CalledProcessError as e:
        raise RuntimeError("❌ Build failed after all recovery attempts.") from e