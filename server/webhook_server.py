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

    # -------------------------------------------------
    # Validate GitHub Push Event
    # -------------------------------------------------
    if "repository" not in payload:

        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "Invalid webhook payload"
            }
        )

    repo_url = (
        payload["repository"]
        ["clone_url"]
    )

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

        # -------------------------------------------------
        # Clone Repository
        # -------------------------------------------------
        print("\n📥 Cloning repository...\n")

        repo_root = clone_repository(repo_url)

        # -------------------------------------------------
        # Analyze Repository
        # -------------------------------------------------
        print("\n🔍 Running analyzer...\n")

        analysis_result = analyze_repository(
            str(repo_root)
        )

        print("✅ Analysis completed")

        # -------------------------------------------------
        # Generate GitHub Actions
        # -------------------------------------------------
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

        # -------------------------------------------------
        # Generate Dockerfiles
        # -------------------------------------------------
        print(
            "\n🐳 Generating Dockerfiles...\n"
        )

        for service in analysis_result["services"]:

            if service["deployable"]:

                generate_dockerfile(
                    service,
                    repo_root
                )

        print("✅ Dockerfiles generated")

        # -------------------------------------------------
        # Commit Changes
        # -------------------------------------------------
        print(
            "\n📦 Committing generated files...\n"
        )

        commit_result = git_commit(
            repo_root,
            "Add generated DevSecOps automation"
        )

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

        print("✅ Git commit successful")

        # -------------------------------------------------
        # Push Changes
        # -------------------------------------------------
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

        # -------------------------------------------------
        # Success Response
        # -------------------------------------------------
        return {

            "success": True,

            "repository": repo_url,

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

            "docker_generated": True,

            "git_push": True
        }

    except Exception as e:

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