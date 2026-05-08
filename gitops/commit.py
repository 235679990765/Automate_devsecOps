import subprocess


def git_commit(repo_path, message):

    try:

        subprocess.run(
            ["git", "add", "."],
            cwd=repo_path,
            check=True
        )

        result = subprocess.run(
            [
                "git",
                "status",
                "--porcelain"
            ],
            cwd=repo_path,
            capture_output=True,
            text=True
        )

        # Nothing changed
        if not result.stdout.strip():

            return {
                "success": True,
                "skipped": True,
                "message": "nothing to commit"
            }

        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                message
            ],
            cwd=repo_path,
            check=True
        )

        return {
            "success": True,
            "skipped": False
        }

    except subprocess.CalledProcessError as e:

        return {
            "success": False,
            "error": str(e)
        }