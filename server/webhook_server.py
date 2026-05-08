import os
import shutil
import tempfile
import subprocess

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from analyzer.analyzer import analyze_repository

from generators.github_actions import (
    GitHubActionsGenerator
)

from docker.generator import generate_dockerfile

from gitops.commit import git_commit
from gitops.push import git_push


app = FastAPI()


# =====================================================
# Helpers
# =====================================================

def clone_repository(repo_url: str):

    temp_dir = tempfile.mkdtemp()

    subprocess.run(
        [
            "git",
            "clone",
            repo_url,
            temp_dir
        ],
        check=True
    )

    return Path(temp_dir)


def cleanup(path: Path):

    try:
        shutil.rmtree(path)
    except Exception:
        pass


# =====================================================
# Health Endpoint
# =====================================================

@app.get("/")
def health():

    return {
        "status": "running",
        "service": "DevSecOps Webhook Server"
    }


# =====================================================
# GitHub Webhook
# =====================================================

@app.post("/webhook/github")
async def github_webhook(request: Request):

    payload = await request.json()

    # =================================================
    # Ignore invalid payloads
    # =================================================
    if "repository" not in payload:

        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "Invalid webhook payload"
            }
        )

    # =================================================
    # Prevent infinite webhook loop
    # =================================================
    head_commit = payload.get(
        "head_commit",
        {}
    )

    commit_message = head_commit.get(
        "message",
        ""
    )

    if (
        "Add generated DevSecOps automation"
        in commit_message
    ):

        print(
            "\n⚠️ Skipping auto-generated commit"
        )

        return {
            "success": True,
            "skipped": True,
            "reason": "auto-generated commit"
        }

    # =================================================
    # Extract repository URL
    # =================================================
    raw_repo_url = (
        payload["repository"]
        ["clone_url"]
    )

    github_token = os.getenv(
        "GITHUB_TOKEN"
    )

    # Use authenticated clone URL if token exists
    if github_token:

        repo_url = raw_repo_url.replace(
            "https://",
            f"https://{github_token}@"
        )

    else:

        repo_url = raw_repo_url

    # =================================================
    # Branch detection
    # =================================================
    ref = payload.get("ref")

    if ref:
        branch = ref.split("/")[-1]
    else:
        branch = "main"

    print("\n🚀 GitHub Push Detected")
    print(f"📦 Repository: {repo_url}")
    print(f"🌿 Branch: {branch}")

    repo_root = None

    try:

        # =================================================
        # Clone Repository
        # =================================================
        print("\n📥 Cloning repository...\n")

        repo_root = clone_repository(
            repo_url
        )

        # =================================================
        # Analyze Repository
        # =================================================
        print("\n🔍 Running analyzer...\n")

        analysis_result = analyze_repository(
            str(repo_root)
        )

        print("✅ Analysis completed")

        # =================================================
        # Generate GitHub Actions Pipeline
        # =================================================
        print(
            "\n⚙️ Generating CI/CD pipeline...\n"
        )

        pipeline_generator = (
            GitHubActionsGenerator()
        )

        pipeline_result = (
            pipeline_generator.generate(
                analysis_result=analysis_result,
                output_dir=repo_root
            )
        )

        print(
            f"✅ Pipeline generated:\n"
            f"{pipeline_result['path']}"
        )

                # =================================================
        # Generate Dockerfiles
        # =================================================
        print(
            "\n🐳 Generating Dockerfiles...\n"
        )

        docker_generated = []

        for service in analysis_result["services"]:

            if not service["deployable"]:
                continue

            try:

                service_path = (
                    repo_root / service["path"]
                )

                docker_result = generate_dockerfile(
                    service_path=service_path,
                    analysis=service["analysis"]
                )

                print(docker_result)

                if docker_result["status"] == "generated":

                    docker_generated.append(
                        service["service"]
                    )

                    print(
                        f"✅ Dockerfile generated "
                        f"for: {service['service']}"
                    )

                elif docker_result["status"] == "skipped":

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
                    f"⚠️ Docker generation failed "
                    f"for {service['service']}: "
                    f"{docker_error}"
                )

        print("✅ Docker generation stage complete")
        # =================================================
        # Commit Changes
        # =================================================
        print(
            "\n📦 Committing generated files...\n"
        )

        commit_result = git_commit(
            repo_root,
            "Add generated DevSecOps automation"
        )

        # Commit failed
        if not commit_result["success"]:

            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "stage": "git-commit",
                    "error":
                        commit_result["error"]
                }
            )

        # Nothing changed
        if commit_result.get("skipped"):

            print(
                "⚠️ Nothing new to commit"
            )

            return {
                "success": True,
                "skipped": True,
                "reason": "nothing-to-commit"
            }

        print("✅ Git commit successful")

        # =================================================
        # Push Changes
        # =================================================
        print(
            "\n🚀 Pushing generated changes...\n"
        )

        push_result = git_push(
            repo_root,
            branch
        )

        if not push_result["success"]:

            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "stage": "git-push",
                    "error":
                        push_result["error"]
                }
            )

        print("✅ Git push successful")
        print(
            "✅ GitHub Actions pipeline triggered"
        )

        # =================================================
        # Success Response
        # =================================================
        return {

            "success": True,

            "repository": raw_repo_url,

            "branch": branch,

            "analysis": {

                "project_structure":
                    analysis_result[
                        "project_structure"
                    ],

                "services":
                    len(
                        analysis_result[
                            "services"
                        ]
                    )
            },

            "pipeline_generated": True,

            "docker_generated":
                docker_generated,

            "git_push": True
        }

    except Exception as e:

        print(f"\n❌ ERROR: {e}")

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )

    finally:

        if repo_root:

            cleanup(repo_root)