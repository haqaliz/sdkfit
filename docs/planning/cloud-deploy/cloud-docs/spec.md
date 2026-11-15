# Spec: `cloud-docs` (T15)

- **Feature:** `cloud-deploy`
- **PRD:** `docs/planning/cloud-deploy/prd.md` (§ M5)
- **Boundary:** the cloud guide, the README/ARCHITECTURE/CHANGELOG/roadmap/status surfaces and the
  static doc checks. No code or manifest changes.

## In-scope requirements

- `docs/technical/CLOUD.md`: architecture (pods, Postgres `SKIP LOCKED`, ingress edge), image
  build/push, namespace and secrets from the examples, managed DB vs the StatefulSet example,
  `--database-url`/`TENON_DATABASE_URL` and exactly-one-of, bundles on a shared PVC, apply with
  kustomize, TLS, nginx rate limits, HPA/workers, metrics with the bearer token, logs, backups,
  upgrades, stale-recovery semantics and the limits (non-HA example DB, nginx-specific limits,
  CPU-based HPA, single-tenant).
- `README.md`: the `--database-url` form, the Postgres store and a link to the guide; the T14/T15
  shipped status.
- `docs/technical/DEPLOYMENT.md`: a pointer to the Kubernetes guide.
- `ARCHITECTURE.md`, `CLAUDE.md`, `ROADMAP.md`, `CAPABILITY_ROADMAP.md` (T14/T15 rows and a
  "T15 as built" section) and the `CHANGELOG.md` `Unreleased` entry.
- A static test that the guide covers the operator keys and the README links it.

## Out-of-scope

- A docs site, screenshots, Terraform, cluster-specific guides beyond nginx.

## Acceptance criteria

- **AC1 — Guide.** The guide covers build, secrets, DB, bundles, apply, TLS, limits, scaling,
  metrics, backups, upgrades and limits.
- **AC2 — Links/status.** README links the guide and documents the URL form; the status surfaces
  list T14/T15; the changelog has the `Unreleased` entry.
- **AC3 — Test/regression.** The doc test and the full suite pass.
