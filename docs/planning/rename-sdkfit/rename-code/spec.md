# Spec: `rename-code` (T17)

- **Feature:** `rename-sdkfit`
- **PRD:** `docs/planning/rename-sdkfit/prd.md` (§ M1, M2, M5)
- **Boundary:** package/import/CLI/env names, source, tests and the rename invariant.

## In-scope requirements

- `pyproject.toml`: `name = "sdkfit"`, `[project.scripts] sdkfit = "sdkfit.cli:main"`; regenerate
  `uv.lock`.
- `git mv src/tenon src/sdkfit`; update every import, docstring/message, `prog="sdkfit"` and the
  `--version` output to `sdkfit <version>`; the `_serve_command` child import.
- Env vars `TENON_*` → `SDKFIT_*` in source/tests/docs/Compose/K8s; no `tenon` alias.
- Tests: imports, fixture emails/names, expected CLI strings; a rename invariant asserting no
  `tenon`/`TENON_` in the shipped code/CLI/Docker/K8s/scripts/docs/launch kit (historical
  changelog/planning and the name-check record exempt).
- No behavior change; version stays 0.4.0.

## Out-of-scope

- Ops/docs prose (the other aspects), a version bump, the live publish.

## Acceptance criteria

- **AC1 — Package.** `import sdkfit`, `sdkfit --version` → `sdkfit 0.4.0`, no `tenon` console script.
- **AC2 — Env.** The service reads `SDKFIT_DATABASE_URL`, `SDKFIT_API_TOKEN`,
  `SDKFIT_WEBHOOK_SECRET`, `SDKFIT_APP_ID`, `SDKFIT_APP_INSTALLATION_ID`.
- **AC3 — Invariant.** The shipped surfaces contain no old name; the full suite passes.
