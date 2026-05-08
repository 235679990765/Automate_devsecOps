import re

from pathlib import Path


SECRET_PATTERNS = {

    "aws_key":
        r"AKIA[0-9A-Z]{16}",

    "github_token":
        r"github_pat_[A-Za-z0-9_]+",

    "private_key":
        r"-----BEGIN PRIVATE KEY-----",

    "generic_secret":
        r"(?i)(secret|token|apikey|api_key)\s*[:=]\s*[\"'][^\"']+[\"']"
}


IGNORED_DIRS = {

    ".git",
    "node_modules",
    "__pycache__",
    "venv",
    ".venv"
}


def detect_secrets(repo: Path):

    findings = []

    for file in repo.rglob("*"):

        if not file.is_file():
            continue

        if any(
            part in IGNORED_DIRS
            for part in file.parts
        ):
            continue

        try:

            content = file.read_text(
                errors="ignore"
            )

        except Exception:
            continue

        for name, pattern in (
            SECRET_PATTERNS.items()
        ):

            matches = re.findall(
                pattern,
                content
            )

            if matches:

                findings.append({

                    "type":
                        name,

                    "file":
                        str(file),

                    "matches":
                        len(matches)
                })

    return findings