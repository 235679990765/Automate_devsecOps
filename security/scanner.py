from pathlib import Path

from security.logger import (
    SecurityLogger
)

from security.secrets import (
    detect_secrets
)

from security.docker_scan import (
    scan_dockerfile
)

from security.dependency_scan import (
    scan_dependencies
)

from security.policy_engine import (
    PolicyEngine
)

from security.risk_engine import (
    RiskEngine
)


class SecurityScanner:

    def __init__(self):

        self.logger = SecurityLogger()

        self.policy_engine = (
            PolicyEngine()
        )

        self.risk_engine = (
            RiskEngine()
        )

    def scan(
        self,
        repo_path
    ):

        repo = Path(repo_path)

        self.logger.log(
            "INFO",
            "SCAN",
            "Starting security scan"
        )

        # ============================================
        # Secret Scan
        # ============================================

        secrets = detect_secrets(repo)

        # ============================================
        # Docker Scan
        # ============================================

        docker_risks = scan_dockerfile(
            repo
        )

        # ============================================
        # Dependency Scan
        # ============================================

        dependency_risks = (
            scan_dependencies(repo)
        )

        # ============================================
        # Policy Evaluation
        # ============================================

        policy_violations = (
            self.policy_engine.evaluate(
                docker_risks,
                dependency_risks
            )
        )

        # ============================================
        # Risk Engine
        # ============================================

        risk_report = (
            self.risk_engine.calculate(
                secrets,
                docker_risks,
                dependency_risks,
                policy_violations
            )
        )

        # ============================================
        # Logging
        # ============================================

        self.logger.log(
            "INFO",
            "RISK",
            f"Risk level: "
            f"{risk_report['risk_level']}",
            risk_report
        )

        self.logger.log(
            "INFO",
            "SCAN",
            "Security scan completed"
        )

        return {

            "risk_report":
                risk_report,

            "secrets":
                secrets,

            "docker_risks":
                docker_risks,

            "dependency_risks":
                dependency_risks,

            "policy_violations":
                policy_violations,

            "logs":
                self.logger.export()
        }