class RiskEngine:

    def calculate(
        self,
        secrets,
        docker_risks,
        dependency_risks,
        policy_violations
    ):

        score = 0

        summary = {

            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }

        findings = []

        # ============================================
        # Secrets
        # ============================================

        for secret in secrets:

            score += 25

            summary["critical"] += 1

            findings.append({

                "severity":
                    "CRITICAL",

                "category":
                    "SECRET",

                "details":
                    secret
            })

        # ============================================
        # Docker
        # ============================================

        for risk in docker_risks:

            severity = risk["severity"]

            if severity == "HIGH":

                score += 20
                summary["high"] += 1

            elif severity == "MEDIUM":

                score += 10
                summary["medium"] += 1

            else:

                score += 5
                summary["low"] += 1

            findings.append({

                "severity":
                    severity,

                "category":
                    "DOCKER",

                "details":
                    risk
            })

        # ============================================
        # Dependencies
        # ============================================

        for dep in dependency_risks:

            severity = dep["severity"]

            if severity == "HIGH":

                score += 20
                summary["high"] += 1

            elif severity == "MEDIUM":

                score += 10
                summary["medium"] += 1

            else:

                score += 5
                summary["low"] += 1

            findings.append({

                "severity":
                    severity,

                "category":
                    "DEPENDENCY",

                "details":
                    dep
            })

        # ============================================
        # Policies
        # ============================================

        for violation in policy_violations:

            score += 15

            summary["high"] += 1

            findings.append({

                "severity":
                    "HIGH",

                "category":
                    "POLICY",

                "details":
                    violation
            })

        # ============================================
        # Final Level
        # ============================================

        if score >= 80:

            level = "CRITICAL"

        elif score >= 50:

            level = "HIGH"

        elif score >= 20:

            level = "MEDIUM"

        else:

            level = "LOW"

        return {

            "risk_score":
                min(score, 100),

            "risk_level":
                level,

            "summary":
                summary,

            "findings":
                findings
        }