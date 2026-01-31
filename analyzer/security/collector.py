from analyzer.security.secrets import scan_secrets
from analyzer.security.dependencies import scan_dependency_risks
from analyzer.security.config import scan_config

def collect_security_facts(repo, language):
    secrets = scan_secrets(repo)
    dep_risks = scan_dependency_risks(repo, language)
    config_risks = scan_config(repo)

    risk_level = "LOW"
    if secrets:
        risk_level = "HIGH"
    elif dep_risks or config_risks:
        risk_level = "MEDIUM"

    return {
        "risk_level": risk_level,
        "secrets_found": secrets,
        "dependency_risks": dep_risks,
        "config_risks": config_risks
    }
