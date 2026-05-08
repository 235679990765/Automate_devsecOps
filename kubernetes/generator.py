from pathlib import Path

from kubernetes.deployment import (
    generate_deployment
)

from kubernetes.service import (
    generate_service
)

from kubernetes.ingress import (
    generate_ingress
)

from kubernetes.hpa import (
    generate_hpa
)

from kubernetes.namespace import (
    generate_namespace
)

from kubernetes.network_policy import (
    generate_network_policy
)

from kubernetes.pdb import (
    generate_pdb
)

from kubernetes.resource_quota import (
    generate_resource_quota
)


class KubernetesGenerator:

    def generate(
        self,
        service,
        output_dir
    ):

        service_name = (
            service["service"]
        )

        k8s_dir = (
            Path(output_dir)
            / "k8s"
            / service_name
        )

        k8s_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        deployment = generate_deployment(
            service
        )

        svc = generate_service(
            service
        )

        ingress = generate_ingress(
            service
        )

        hpa = generate_hpa(
            service
        )

        namespace = (
            generate_namespace(
                service
            )
        )

        network_policy = (
            generate_network_policy(
                service
            )
        )

        pdb = generate_pdb(
            service
        )

        quota = (
            generate_resource_quota(
                service
            )
        )

        files = {

            "deployment.yaml":
                deployment,

            "service.yaml":
                svc,

            "ingress.yaml":
                ingress,

            "hpa.yaml":
                hpa,

            "namespace.yaml":
                namespace,

            "network-policy.yaml":
                network_policy,

            "pdb.yaml":
                pdb,

            "resource-quota.yaml":
                quota
        }

        for name, content in (
            files.items()
        ):

            (
                k8s_dir / name
            ).write_text(content)

        return {

            "generated": True,

            "path": str(k8s_dir),

            "files": list(
                files.keys()
            )
        }