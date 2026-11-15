# PRD: Hardened cloud deployment (T15)

- **Slug:** `cloud-deploy`
- **Capability:** **T15 Hardened cloud deployment** — beyond the Compose/Caddy MVP
- **Milestone:** after v0.3.0
- **Status:** draft for review
- **Card:** `docs/planning/_card/issue.md`

## Problem Statement

T13a/T13b ship a single-host Compose stack: the service behind Caddy, SQLite, in-process worker
threads. That is deployable, but not cloud-scale: one process, one writable volume, no shared
store/queue, no horizontal scaling, and rate limiting is left to the proxy.

T15 hardens the service for Kubernetes with a **Postgres store/queue** and multi-replica-safe claims:
several service pods each run in-process workers over `FOR UPDATE SKIP LOCKED`, an Ingress provides
TLS and rate limits, and an HPA scales on CPU. The bundle/key mounts, readiness/liveness, metrics
scrape annotations, backups and upgrades are documented.

The SQLite path stays the local/single-host default; Postgres is an optional `[postgres]` extra. No
SaaS control plane, multi-tenant auth, web UI or new locator/provider behavior.

**For whom:** an operator deploying the service on Kubernetes, the provider running many migrations,
and the customer whose PRs the service opens.

## Goals & Success Metrics

1. **A shared store.** `PostgresRunStore` implements the same public store API as `RunStore`
   (create/claim/requeue/finish/get/list/events/idempotency/ping/counts/recover/close) with
   `FOR UPDATE SKIP LOCKED` claims; an optional `psycopg` extra.
2. **Safe multi-replica.** Two pods claim distinct runs; a startup recovery only re-queues running
   rows older than a stale lease, never a live peer's run.
3. **A Kubernetes deployment.** Deployment (2 replicas, non-root/read-only, probes, resources),
   Service, Ingress (TLS + nginx rate-limit annotations), HPA, Postgres (a portable StatefulSet
   example or a managed-DB note), Secret/ConfigMap examples, bundle/key mounts, metrics scrape
   annotations, and a kustomization.
4. **One CLI switch.** `--database-url`/`TENON_DATABASE_URL` selects Postgres; exactly one of
   `--db`/`--database-url` is required; a missing driver is a named error. SQLite behavior is
   unchanged.
5. **Docs.** A cloud/kubernetes guide (build/push, secrets, DB, bundles, apply, TLS, rate limits,
   scaling, metrics, backups, upgrades, limits) and README/ARCHITECTURE/CHANGELOG updates.
6. **Offline/static tests.** The Postgres store against a fake driver; the CLI selection/errors;
   static manifest invariants; all prior tests green. No cluster/DB in pytest.

## Requirements

### Must have

- **M1 — Postgres store.** `src/tenon/service/postgres.py`: `PostgresRunStore(dsn, *, connect=None)`
  with the same `Run`/`Event` return shapes and public methods as `RunStore`.
  - Schema: `runs(id text pk, bundle text, status text, created_at timestamptz, started_at,
    finished_at, exit int, report jsonb, error text, idempotency_key text unique, attempts int,
    cancel_requested bool)`, `events(id bigserial pk, delivery text unique, event, action,
    installation, received_at, payload jsonb)`; created on open.
  - `claim_next`: `SELECT id ... WHERE status='queued' ORDER BY created_at, id FOR UPDATE SKIP
    LOCKED LIMIT 1`, then an `UPDATE ... SET status='running', started_at=now(), attempts=attempts+1
    RETURNING ...` in one transaction.
  - `create_run` idempotency via `ON CONFLICT (idempotency_key) DO NOTHING` + a select; `requeue`;
    `finish` (`succeeded|failed|cancelled`); `request_cancel`/`cancel_requested`; `counts`; `recover`
    (only running rows whose `started_at` is older than the stale lease, via a `--run-timeout`-based
    grace; a `recover(older_than)` argument); `ping` (`SELECT 1 FROM runs LIMIT 1`); `close`.
  - A `Store` protocol in `store.py` (or `types.py`) that both stores satisfy; `Worker`/`Api` type
    hints use it; `psycopg[binary]` in an optional `[postgres]` extra and the dev group for tests.
- **M2 — CLI.** `provider serve --database-url URL`/`TENON_DATABASE_URL`; exactly one of `--db`/
  `--database-url`; a factory returns the SQLite or Postgres store; a missing `psycopg` is a named
  usage/config error; `store.recover()` with the stale lease; the worker/Api unchanged otherwise.
- **M3 — Kubernetes.** `deploy/k8s/`: `deployment.yaml` (2 replicas, the image, `TENON_DATABASE_URL`
  from a secret, the app identity env, bundle/key mounts, non-root/read-only/dropped caps, readiness
  `/ready`, liveness `/health`, resources, `--workers`), `service.yaml` (ClusterIP + metrics scrape
  annotations), `ingress.yaml` (TLS host + nginx `limit-rps`/`limit-burst`), `hpa.yaml` (CPU 2..10),
  `postgres.yaml` (a StatefulSet + Service + PVC example with a note to prefer a managed DB),
  `secret.example.yaml` (placeholders, never real values), `configmap.example.yaml` (bundle names?),
  `kustomization.yaml`. The manifests must not contain real secrets.
- **M4 — Rate limiting/observability.** Ingress annotations for per-IP/route limits; metrics scrape
  annotations on the Service/pods; stdout/stderr logs; the guide covers the scrape and limits.
- **M5 — Docs.** `docs/technical/CLOUD.md` (or a Kubernetes section in `DEPLOYMENT.md`): image
  build/push, namespace/secrets, Postgres (managed or example), bundles PVC, apply, TLS, rate
  limits, HPA/workers, metrics/backups/upgrades, the stale-recovery semantics and limits.
  README/ARCHITECTURE/CHANGELOG `Unreleased`/capability roadmap T15.
- **M6 — Tests.** A fake psycopg connection/cursor that records SQL and returns the expected rows;
  the store's create/claim/idempotency/requeue/finish/cancel/counts/recover/ping; the CLI selection
  and missing-driver error; static manifest invariants (replicas/probes/security/ingress rate
  limits/HPA/Postgres/no secrets); all prior tests green. Offline.

### Should have

- **S1 — Same semantics.** The two stores return the same `Run`/`Event` values and status rules.
- **S2 — Least privilege.** K8s securityContext (non-root, read-only root, dropped caps), secrets
  from Secret/Env, no secret literals in manifests.
- **S3 — One image.** The same image runs locally (SQLite) and on K8s (Postgres) via flags/env.

### Nice to have

- **N1 — Redis queue/workers**; not now.
- **N2 — Managed-DB IaC (Terraform/Cloud SQL)**; docs only.
- **N3 — A real cluster smoke test in CI**; the release workflow remains the integration path.

## Data Model

Same `Run`/`Event` values; a `Store` protocol. Postgres adds `timestamptz`/`jsonb` columns and a
stale-recovery threshold.

## API Contract

```sh
tenon provider serve --bundles /data/bundles --database-url "$TENON_DATABASE_URL" \
  --api-token "$TOKEN" --webhook-secret "$SECRET" --workers 4
```

The K8s Deployment sets `TENON_DATABASE_URL` from a Secret and mounts the bundles/key read-only.

## Technical Considerations

- **Why Postgres + SKIP LOCKED.** Multiple pods need a shared atomic claim; `SKIP LOCKED` is the
  standard queue primitive without a new broker.
- **Why stale recovery.** A startup `recover()` that re-queues every running row would steal a live
  peer's run; only rows older than a lease grace are recovered.
- **Why the ingress owns rate limits.** Caddy/nginx already terminate TLS; app token buckets would
  duplicate policy and need shared state to be effective across pods.
- **Why a portable Postgres StatefulSet example.** It keeps the manifests self-contained; a managed DB
  is the recommended production path and the guide says so.
- **Why static tests.** The manifests are deployment artifacts; pytest checks their invariants
  offline, the first cluster apply is the integration test.

## Risks & Open Questions

- **Fake driver fidelity.** The SQL is tested against a fake; a real Postgres run is the operator's
  first step. The SQL is standard (`SKIP LOCKED` requires PG 9.5+).
- **In-cluster Postgres is not HA.** The example is for a portable demo; use a managed HA database in
  production (documented).
- **Ingress annotations are nginx-specific.** Another controller needs equivalent limits (documented).
- **Recovery lease.** A long run beyond the lease grace can be recovered while still alive; set the
  grace above the run timeout. Documented.
- **No HPA on queue depth.** CPU-based HPA is the MVP; a queue-length metric is a later card.
- **Open question — should the Postgres driver be required?** No; an optional `[postgres]` extra; the
  SQLite install is unchanged.
- **Open question — should the manifests include a namespace?** A kustomization with the named
  resources; the operator creates the namespace (documented).

## Out of Scope

- SaaS control plane, multi-tenant auth, billing, a web UI.
- Redis/Celery, managed-DB Terraform, a real-cluster CI job.
- New locators/provider features; changes to the proof/PR semantics.

## Aspect Proposals (for `tech-plan`)

| Aspect | Boundary |
|---|---|
| `postgres-store` | The `Store` protocol, `PostgresRunStore`, the optional dependency, the fake-driver tests. No CLI/manifests. |
| `postgres-cli` | `--database-url`/env, the store factory, `recover` wiring, CLI/worker/API tests. No store internals. |
| `k8s-manifests` | `deploy/k8s/*`, the static manifest tests. No docs. |
| `cloud-docs` | The cloud guide, README/ARCHITECTURE/CHANGELOG/roadmap, status. |

## Self-critique (prd-generator pass)

| Dimension | Rating | Note |
|---|---|---|
| Problem definition | 🟢 | The Compose MVP is single-host and single-process. |
| User understanding | 🟢 | Operator/provider/customer; the K8s flow is concrete. |
| Success metrics | 🟢 | Postgres store, safe claims/recovery, manifests, one CLI switch, docs, offline tests. |
| Scope clarity | 🟢 | K8s + Postgres only; no SaaS/Redis/managed IaC. |
| Edge cases & risks | 🟡 | Fake-driver fidelity, non-HA example DB and lease recovery are real; documented. |
| Stakeholder alignment | 🟡 | Solo project; the review gate is the approver. |
| Feasibility | 🟢 | Reuses the store/worker/API seams; one optional dependency. |
| Go-to-market | 🟢 | The service becomes horizontally scalable on a standard cloud. |

**Areas to strengthen before sharing:** the in-cluster Postgres is a demo, not an HA database; the
guide recommends managed Postgres. The store SQL is tested against a fake, not a live server.

**The question I would want answered before greenlighting this:** *If two pods start at once, can they
run the same queued run twice?* The answer this card records: no; the claim is a
`FOR UPDATE SKIP LOCKED` transaction that sets the row running, so only one pod gets it. The stale
recovery never steals a row younger than the lease grace.
