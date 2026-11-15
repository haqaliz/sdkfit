# Deploying on Kubernetes

T15 turns the single-host Compose stack into a horizontally scalable deployment: several service
pods share one Postgres run queue, an Ingress terminates TLS and rate-limits, and an HPA scales the
pods. The image is the same one used locally; only the store changes.

```
Internet -> Ingress (TLS, nginx rate limits) -> Service -> N pods (API + workers)
                                                              |
                                                              v
                                                        Postgres (SKIP LOCKED queue)
```

Each pod runs the HTTP API and `--workers` in-process worker threads. A claim is one
`FOR UPDATE SKIP LOCKED` statement, so two pods never run the same queued run; retries, cancel,
metrics and the report are the T13b behavior, unchanged.

For the single-VM Compose/Caddy path see `DEPLOYMENT.md`. For the local service behavior see the
README.

## Prerequisites

- A Kubernetes cluster (1.27+) and `kubectl`.
- An nginx ingress controller (`ingressClassName: nginx`) and a TLS story: cert-manager, or your own
  `kubernetes.io/tls` secret.
- `metrics-server` if you want the HPA to read CPU.
- A container registry you can push to.
- The `deploy/k8s` manifests from this repo.

## Build and push the image

The Dockerfile installs the `app` and `postgres` extras, so one image runs SQLite locally and
Postgres in the cluster.

```sh
docker build -t ghcr.io/OWNER/tenon:X.Y.Z .
docker push ghcr.io/OWNER/tenon:X.Y.Z
```

Set that reference in `deploy/k8s/deployment.yaml` (`image:`). Pin a version tag, not `latest`.

## Namespace and secrets

The manifests expect a namespace of your choice; the examples have no `metadata.namespace`.

```sh
kubectl create namespace tenon
kubectl -n tenon apply -f deploy/k8s/secret.example.yaml   # after filling it
kubectl -n tenon apply -f deploy/k8s/configmap.example.yaml
```

Before applying, copy the examples and replace every placeholder:

- `tenon-secrets` / `api-token`: a long random bearer token (clients and Prometheus use it).
- `tenon-secrets` / `webhook-secret`: the GitHub App webhook secret (used by `--trigger`).
- `tenon-secrets` / `database-url`: `postgresql://tenon:<password>@<host>:5432/tenon`.
- `tenon-secrets` / `postgres-password`: the same password, only for the example Postgres.
- `tenon-app-key` / `app.pem`: the GitHub App private key, mounted at `/secrets/app.pem`.
- `tenon-config` / `app-id`, `app-installation-id`: the GitHub App identity.

Never commit the filled files. Rotate the token and webhook secret the same way as in
`DEPLOYMENT.md` (update the Secret, restart the pods, update API clients and GitHub).

## Database

Use a managed, backed-up Postgres in production and set `database-url` to it. The
`deploy/k8s/postgres.yaml` StatefulSet is a portable, **single-instance** example for demos and small
installs: it has one replica, no failover and no backups of its own.

```sh
kubectl -n tenon apply -f deploy/k8s/postgres.yaml   # optional demo database
```

The service creates the `runs` and `events` tables and the queue index on first open
(`CREATE ... IF NOT EXISTS`); it needs no migration job. `SKIP LOCKED` requires Postgres 9.5+. The
Deployment passes the secret key to `provider serve` as `TENON_DATABASE_URL`; the equivalent flag is
`--database-url`.

Startup recovery only re-queues a `running` row whose `started_at` is older than `now - --run-timeout`
(or cancels a run whose cancel was requested). A live peer's run is never stolen. A run that crashed
just before the cutoff stays `running` until a later restart or pod start; monitor `tenon_runs`.

## Bundles

The Deployment mounts the `tenon-bundles` PVC read-only at `/data/bundles`. The claim requests
`ReadWriteMany`; provide a storage class that supports it (a cloud file share or NFS). Populate it
before scaling up, for example:

```sh
kubectl -n tenon run bundles --rm -it --image=busybox \
  --overrides='{"spec":{"volumes":[{"name":"b","persistentVolumeClaim":{"claimName":"tenon-bundles"}}],"containers":[{"name":"bundles","image":"busybox","stdin":true,"tty":true,"volumeMounts":[{"name":"b","mountPath":"/data"}]}]}}' \
  -- sh
# then copy bundle JSON files into /data (or populate the share from a job/bucket sync)
```

A bundle name is still confined to the directory and must end in `.json`; a deleted bundle is a
failed run, not a crash.

## Apply

```sh
kubectl -n tenon apply -k deploy/k8s
kubectl -n tenon rollout status deployment/tenon
kubectl -n tenon get pods,svc,hpa,ingress
```

Edit `ingress.yaml` first: replace `tenon.example.com` with your DNS name (in `tls.hosts` and
`rules.host`). Point the DNS record at the ingress controller's address.

The kustomization applies the Deployment, Service, Ingress, HPA and bundle PVC. Secrets, the
ConfigMap and the optional Postgres are applied separately so placeholders never ship by accident.

## TLS

- **cert-manager:** add a `ClusterIssuer` and the usual
  `cert-manager.io/cluster-issuer: letsencrypt-prod` annotation to `ingress.yaml`; it fills the
  `tenon-tls` secret.
- **Bring your own certificate:**

  ```sh
  kubectl -n tenon create secret tls tenon-tls --cert=fullchain.pem --key=privkey.pem
  ```

The ingress redirects HTTP to HTTPS (`ssl-redirect`). Nothing inside the cluster is TLS; the Service
is ClusterIP-only.

## Rate limits

The Ingress carries nginx per-IP limits: 10 requests/second
(`nginx.ingress.kubernetes.io/limit-rps: "10"`) with a 5x burst multiplier and 20 concurrent
connections. Tune them to your GitHub App rate limit; the webhook, `/runs` and the
read-only API share the budget. These annotations are **nginx-specific**: another controller needs
its own equivalent (for example an Envoy `RateLimitPolicy`), because the per-pod in-process workers
cannot enforce a global limit. The bearer token and webhook HMAC remain the authentication boundary.

## Scaling and workers

The HorizontalPodAutoscaler (HPA) scales 2..10 pods on 70% CPU. Each pod also runs `--workers 4`; total concurrency is
pods × workers. All pods claim from the same Postgres queue, so scaling out adds throughput without
duplicating a run. Raise `workers` only as far as the installation's GitHub rate limit allows: every
run clones and may push and open PRs.

CPU is the MVP scaling signal. A queue-depth metric would scale on backlog; that is a later card.

## Metrics and logs

The pod template and Service carry Prometheus scrape annotations, but `GET /metrics` is bearer-only,
so the scrape job must send the token (the annotations alone cannot). Use the T13b Prometheus job
with a `credentials_file` holding the API token, as in `DEPLOYMENT.md`:

```yaml
scrape_configs:
  - job_name: tenon
    scheme: https
    authorization:
      credentials_file: /etc/prometheus/tenon-token
    static_configs:
      - targets: ["tenon.example.com"]
```

The service logs JSON-ish structured lines to stdout/stderr; the token, webhook secret and key
contents are never logged.

```sh
kubectl -n tenon logs deployment/tenon --tail=100
```

## Backups

- **Database:** use the managed service's point-in-time recovery. For the example StatefulSet,
  schedule `pg_dump -U tenon -d tenon` to object storage, or snapshot the PVC; a single PVC is not a
  backup.
- **Bundles:** keep the bundle directory in version control or a versioned object store; the PVC is
  a cache.
- **Secrets:** store the source of truth in your secret manager, not in the cluster alone.

The store is durable: a pod restart does not lose run history, and startup recovery re-queues
stranded rows past the lease.

## Upgrades

1. Back up the database.
2. Push the new image tag and update `image:` in `deployment.yaml`.
3. `kubectl -n tenon apply -k deploy/k8s`; the rolling update keeps at least one pod serving.
4. Watch `kubectl -n tenon rollout status deployment/tenon` and the logs.
5. Keep the old image tag until the new pods are ready; roll back by re-applying the previous image.

The schema only adds tables/indexes (`IF NOT EXISTS`), so an upgrade does not rewrite run history.

## Local checks

```sh
kubectl kustomize deploy/k8s          # renders the manifests
uv run pytest tests/test_k8s.py       # static invariants, offline
```

The first real apply is the integration test; there is no cluster or Postgres in pytest.

## Known limits

- The in-cluster Postgres example is single-instance with no HA or backups; use a managed database.
- Ingress rate limits are nginx-specific and per-IP; other controllers need their own policy.
- The recovery lease is `--run-timeout`; a run that crashes just under the cutoff is recovered at the
  next pod start, not immediately.
- The HPA scales on CPU, not queue depth.
- The service is single-tenant: one API token, one GitHub App, one bundle directory.
- No Redis/broker, no SaaS control plane, no managed-database Terraform.
