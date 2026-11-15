# Spec: `k8s-manifests` (T15)

- **Feature:** `cloud-deploy`
- **PRD:** `docs/planning/cloud-deploy/prd.md` (§ M3–M4, M6)
- **Boundary:** `deploy/k8s/*`, the image's `postgres` extra and the static manifest tests. No CLI or
  store internals and no prose docs.

## In-scope requirements

- `deploy/k8s/deployment.yaml`: 2 replicas; the image; `TENON_DATABASE_URL`/`TENON_API_TOKEN`/
  `TENON_WEBHOOK_SECRET` from the `tenon-secrets` Secret; the app identity from `tenon-config` and a
  `tenon-app-key` Secret; `--bundles /data/bundles --host 0.0.0.0 --port 8080 --workers 4`;
  readiness `/ready`, liveness `/health`; non-root, read-only root filesystem, dropped capabilities,
  no privilege escalation; resource requests/limits; the bundles PVC, key Secret and a `/tmp`
  emptyDir mounted; metrics scrape annotations on the pod template.
- `deploy/k8s/service.yaml`: ClusterIP on `http`/8080 plus Prometheus scrape annotations.
- `deploy/k8s/ingress.yaml`: TLS host, `nginx` ingress class and per-IP rate-limit annotations.
- `deploy/k8s/hpa.yaml`: CPU-based autoscaling, 2..10 replicas.
- `deploy/k8s/postgres.yaml`: a portable single-instance Postgres StatefulSet + Service + PVC
  example (a managed database is the documented production path).
- `deploy/k8s/bundles-pvc.yaml`: the shared read-only bundle volume.
- `deploy/k8s/secret.example.yaml` / `configmap.example.yaml`: placeholders only, never real values.
- `deploy/k8s/kustomization.yaml`: the deployment/service/ingress/hpa/PVC resources.
- `Dockerfile`: install the `postgres` extra so one image runs both stores.
- `tests/test_k8s.py`: parse every manifest and assert the above, plus no secret literals in the
  Deployment. Offline.

## Out-of-scope

- Applying to a cluster, a namespace resource, Terraform/managed-DB IaC, ingress controllers other
  than nginx, the cloud guide.

## Acceptance criteria

- **AC1 — Deployment.** 2 replicas; the DB URL from a Secret; probes; non-root/read-only/dropped
  caps; resources; the bundle/key/tmp mounts; scrape annotations.
- **AC2 — Edge.** A ClusterIP Service on 8080; an Ingress with TLS and nginx rate limits.
- **AC3 — Scaling.** An HPA with CPU utilization and 2..10 replicas.
- **AC4 — Data.** A Postgres StatefulSet example with a PVC; a bundle PVC; placeholder Secret and
  ConfigMap examples; a kustomization listing the resources.
- **AC5 — Safety.** No secret literal in the Deployment; the image installs `postgres`.
- **AC6 — Regression.** All prior tests green.
