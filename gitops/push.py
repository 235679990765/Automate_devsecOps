import subprocess


def git_push(repo_path, branch="main"):

    try:

        subprocess.run(
            [
                "git",
                "push",
                "origin",
                branch
            ],
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