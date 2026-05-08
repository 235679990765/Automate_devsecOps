from pathlib import Path


def scan_dockerfile(repo: Path):

    dockerfile = repo / "Dockerfile"

    risks = []

    if not dockerfile.exists():

        return risks

    content = dockerfile.read_text(
        errors="ignore"
    )

    if ":latest" in content:

        risks.append({
            "severity": "MEDIUM",
            "message": "Avoid latest tag"
        })

    if "USER root" in content:

        risks.append({
            "severity": "HIGH",
            "message": "Container runs as root"
        })

    if "sudo" in content:

        risks.append({
            "severity": "MEDIUM",
            "message": "sudo usage detected"
        })

    if "HEALTHCHECK" not in content:

        risks.append({
            "severity": "LOW",
            "message": "No HEALTHCHECK configured"
        })

    return risks