"""Static invariants for the Kubernetes deployment artifacts."""

from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
K8S = ROOT / "deploy" / "k8s"


def a_documents(name: str) -> list[dict]:
    text = (K8S / name).read_text(encoding="utf-8")
    return [doc for doc in yaml.safe_load_all(text) if doc]


def a_by_kind(name: str, kind: str) -> dict:
    return next(doc for doc in a_documents(name) if doc["kind"] == kind)


# Spec AC1: two hardened replicas share one Postgres queue and the bundle/key mounts.
def test_the_deployment_is_a_hardened_two_replica_pod():
    deployment = a_by_kind("deployment.yaml", "Deployment")

    assert deployment["spec"]["replicas"] == 2
    pod = deployment["spec"]["template"]["spec"]
    assert pod["securityContext"]["runAsNonRoot"] is True
    container = pod["containers"][0]
    container_security = container["securityContext"]
    assert container_security["readOnlyRootFilesystem"] is True
    assert container_security["allowPrivilegeEscalation"] is False
    assert container_security["capabilities"]["drop"] == ["ALL"]
    assert container["readinessProbe"]["httpGet"]["path"] == "/ready"
    assert container["livenessProbe"]["httpGet"]["path"] == "/health"
    assert container["resources"]["requests"]
    assert container["resources"]["limits"]

    env = {entry["name"]: entry for entry in container["env"]}
    database = env["TENON_DATABASE_URL"]["valueFrom"]["secretKeyRef"]
    assert database == {"name": "tenon-secrets", "key": "database-url"}
    assert env["TENON_API_TOKEN"]["valueFrom"]["secretKeyRef"]["name"] == (
        "tenon-secrets"
    )
    assert env["TENON_WEBHOOK_SECRET"]["valueFrom"]["secretKeyRef"]["name"] == (
        "tenon-secrets"
    )

    args = container["args"]
    for value in (
        "--bundles",
        "/data/bundles",
        "--host",
        "0.0.0.0",
        "--port",
        "8080",
        "--workers",
        "4",
        "--app-private-key",
        "/secrets/app.pem",
    ):
        assert value in args

    mounts = {mount["name"]: mount for mount in container["volumeMounts"]}
    assert mounts["bundles"]["mountPath"] == "/data/bundles"
    assert mounts["bundles"]["readOnly"] is True
    assert mounts["app-key"]["mountPath"] == "/secrets"
    assert mounts["app-key"]["readOnly"] is True
    assert mounts["tmp"]["mountPath"] == "/tmp"
    volumes = {volume["name"]: volume for volume in pod["volumes"]}
    assert volumes["bundles"]["persistentVolumeClaim"]["claimName"] == (
        "tenon-bundles"
    )
    assert volumes["app-key"]["secret"]["secretName"] == "tenon-app-key"
    assert volumes["tmp"]["emptyDir"] == {}

    annotations = deployment["spec"]["template"]["metadata"]["annotations"]
    assert annotations["prometheus.io/scrape"] == "true"
    assert annotations["prometheus.io/port"] == "8080"


# Spec AC5: the Deployment never carries a literal secret.
def test_the_deployment_has_no_secret_literals():
    deployment = a_by_kind("deployment.yaml", "Deployment")
    container = deployment["spec"]["template"]["spec"]["containers"][0]

    for entry in container["env"]:
        assert "value" not in entry
    assert "stringData" not in (K8S / "deployment.yaml").read_text(encoding="utf-8")


# Spec AC2: one ClusterIP service on 8080, scrapeable by Prometheus.
def test_the_service_is_a_scraped_cluster_ip():
    service = a_by_kind("service.yaml", "Service")

    assert service["spec"]["type"] == "ClusterIP"
    port = service["spec"]["ports"][0]
    assert port["name"] == "http"
    assert port["port"] == 8080
    assert service["metadata"]["annotations"]["prometheus.io/scrape"] == "true"


# Spec AC2: TLS terminates at the ingress, which enforces per-IP rate limits.
def test_the_ingress_has_tls_and_rate_limits():
    ingress = a_by_kind("ingress.yaml", "Ingress")
    annotations = ingress["metadata"]["annotations"]

    assert annotations["nginx.ingress.kubernetes.io/limit-rps"] == "10"
    assert "limit-burst" in " ".join(annotations)
    assert ingress["spec"]["tls"][0]["hosts"]
    rule = ingress["spec"]["rules"][0]
    assert rule["host"]
    backend = rule["http"]["paths"][0]["backend"]["service"]
    assert backend["name"] == "tenon"
    assert backend["port"]["name"] == "http"


# Spec AC3: CPU-based autoscaling inside a bounded range.
def test_the_hpa_scales_on_cpu():
    hpa = a_by_kind("hpa.yaml", "HorizontalPodAutoscaler")

    assert hpa["spec"]["minReplicas"] == 2
    assert hpa["spec"]["maxReplicas"] == 10
    metric = hpa["spec"]["metrics"][0]["resource"]
    assert metric["name"] == "cpu"
    assert metric["target"]["averageUtilization"] == 70


# Spec AC4: a portable Postgres example exists, but is not the production path.
def test_the_postgres_example_is_a_statefulset_with_storage():
    kinds = {doc["kind"] for doc in a_documents("postgres.yaml")}
    assert {"StatefulSet", "Service"} <= kinds

    stateful = a_by_kind("postgres.yaml", "StatefulSet")
    assert stateful["spec"]["serviceName"] == "tenon-postgres"
    container = stateful["spec"]["template"]["spec"]["containers"][0]
    assert container["image"].startswith("postgres:")
    claim = stateful["spec"]["volumeClaimTemplates"][0]
    assert claim["spec"]["resources"]["requests"]["storage"]


# Spec AC4: the bundle volume is shared read-only by every replica.
def test_the_bundles_claim_is_shared():
    pvc = a_by_kind("bundles-pvc.yaml", "PersistentVolumeClaim")

    assert pvc["metadata"]["name"] == "tenon-bundles"
    assert "ReadWriteMany" in pvc["spec"]["accessModes"]


# Spec AC4/AC5: the secret example is placeholders only and the URL points at the DB service.
def test_the_secret_example_holds_placeholders_only():
    docs = a_documents("secret.example.yaml")

    assert {doc["metadata"]["name"] for doc in docs} == {
        "tenon-secrets",
        "tenon-app-key",
    }
    for doc in docs:
        for value in doc["stringData"].values():
            assert "replace" in value.lower()
    database = next(
        doc for doc in docs if doc["metadata"]["name"] == "tenon-secrets"
    )["stringData"]["database-url"]
    assert "tenon-postgres:5432" in database


# Spec AC4: the app identity is operator config, not a baked-in constant.
def test_the_configmap_example_carries_the_app_identity():
    config = a_by_kind("configmap.example.yaml", "ConfigMap")

    assert config["metadata"]["name"] == "tenon-config"
    assert config["data"]["app-id"]
    assert config["data"]["app-installation-id"]


# Spec AC4: kustomize applies the service, edge, scaling and bundle volume together.
def test_the_kustomization_lists_the_workloads():
    kustomization = a_documents("kustomization.yaml")[0]

    assert {
        "deployment.yaml",
        "service.yaml",
        "ingress.yaml",
        "hpa.yaml",
        "bundles-pvc.yaml",
    } <= set(kustomization["resources"])


# Spec AC5: the one image can open the Postgres store.
def test_the_image_installs_the_postgres_extra():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "--extra postgres" in dockerfile
