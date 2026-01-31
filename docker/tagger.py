import subprocess

def get_git_short_sha(repo_root):
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root
        )
        return sha.decode().strip()
    except Exception:
        return "dev"
