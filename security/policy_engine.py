class PolicyEngine:

    def evaluate(
        self,
        docker_risks,
        dependency_risks
    ):

        violations = []

        for risk in docker_risks:

            if risk["severity"] == "HIGH":

                violations.append(
                    f"Docker policy violation: "
                    f"{risk['message']}"
                )

        for dep in dependency_risks:

            if dep["severity"] in [
                "HIGH",
                "CRITICAL"
            ]:

                violations.append(
                    f"Dependency violation: "
                    f"{dep['package']}"
                )

        return violations