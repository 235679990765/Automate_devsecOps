import subprocess


def git_commit(repo_path, message):

    try:

        subprocess.run(
            ["git", "add", "."],
            cwd=repo_path,
            check=True
        )

        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo_path,
            check=True
        )

        return {
            "success": True
        }

    except subprocess.CalledProcessError as e:

        return {
            "success": False,
            "error": str(e)
        }