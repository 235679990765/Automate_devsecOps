from pathlib import Path


def scan_dependencies(repo: Path):

    findings = []

    req = repo / "requirements.txt"

    if req.exists():

        content = req.read_text(
            errors="ignore"
        ).lower()

        if "django==1." in content:

            findings.append({

                "severity":
                    "HIGH",

                "package":
                    "django",

                "issue":
                    "Outdated Django version"
            })

    pkg = repo / "package.json"

    if pkg.exists():

        content = pkg.read_text(
            errors="ignore"
        ).lower()

        if "\"lodash\"" in content:

            findings.append({

                "severity":
                    "MEDIUM",

                "package":
                    "lodash",

                "issue":
                    "Potential vulnerable lodash version"
            })

    return findings