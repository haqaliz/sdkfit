# Card: feat/cloud-deploy

- **Source:** FALLBACK — no GitHub issue (`gh issue list` is empty).
- **Owner:** aliz
- **Type:** feat
- **Capability:** **T15 Hardened cloud deployment** — beyond the Compose/Caddy MVP
- **Milestone:** after v0.3.0
- **State:** T15 shipped 2026-11-16 (Postgres store/queue, Kubernetes manifests, cloud guide; 2,771 tests)
- **Branch:** `feat/cloud-deploy/aliz`
- **Worktree:** `.claude/worktrees/feat-cloud-deploy`

## Brief

T13a/T13b ship a single-host Docker Compose stack: the service behind Caddy, SQLite, in-process
worker threads. That is deployable, but not a cloud-scale deployment: one process, one writable
volume, no shared queue/store, no horizontal scaling, and rate limiting is left to the proxy.

T15 hardens the deployment for a cloud/managed host, with the smallest complete architecture:
- a **deployment target** (Kubernetes manifests or a managed-VM blueprint);
- a **shared store/queue** (Postgres with safe multi-process claims, or a documented SQLite +
  Litestream/backup alternative);
- **rate limiting** at the proxy or in the app;
- an **observability/ops** pass (metrics scrape, logs, health/readiness, backups);
- docs and static/deployment tests.

No SaaS control plane, no multi-tenant auth, no web UI, no new locator/provider capability.

## Constraints carried in from the repo

- T13a/T13b's image, Compose, Caddy, `RunStore`, `Worker`, `Api`, `/metrics` are the base.
- Stdlib-first; a Postgres driver is an optional dependency if chosen.
- Offline tests; deployment manifests are static artifacts, not run in pytest (the release workflow
  remains the integration path).
- `CLAUDE.md` §1–5: no merge/default branch, secrets never in the repo, BYOK.

## Scope fence

Not this card: a hosted SaaS control plane, billing, multi-tenant auth, a web UI, new languages or
provider features, cloud-specific IaC beyond the chosen target.
