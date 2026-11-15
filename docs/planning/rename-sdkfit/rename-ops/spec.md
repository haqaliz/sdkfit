# Spec: `rename-ops` (T17)

- **Feature:** `rename-sdkfit`
- **PRD:** `docs/planning/rename-sdkfit/prd.md` (§ M3, M5)
- **Boundary:** Docker/Compose/Caddy, Kubernetes, scripts and workflows/guides.

## In-scope requirements

- `Dockerfile`: entrypoint/healthcheck names; `docker-compose.yml` service/volumes; `Caddyfile`
  comments.
- `deploy/k8s/*`: resource names/labels (`sdkfit`, `sdkfit-secrets`, `sdkfit-app-key`,
  `sdkfit-config`, `sdkfit-bundles`, `sdkfit-postgres`), env `SDKFIT_*`, image
  `ghcr.io/haqaliz/sdkfit`.
- `scripts/release_check.sh`/`launch_demo.sh`: `uv run sdkfit`, wheel `sdkfit-*`, expected version.
- Release guide/workflow references: repo `haqaliz/sdkfit`, PyPI `sdkfit`, image path.
- Tests: `tests/test_k8s.py`, `tests/test_ci.py` and the demo test updated; no old resource/env names.

## Out-of-scope

- Source/tests (the code aspect), prose docs (the docs aspect), publishing.

## Acceptance criteria

- **AC1 — Container.** The image builds, its entrypoint is `sdkfit`, and `sdkfit --version` works.
- **AC2 — K8s.** The manifests use `sdkfit-*` names, `SDKFIT_*` env and the `sdkfit` image; the
  static tests pass.
- **AC3 — Scripts.** The release check and launch demo use `sdkfit` and pass.
