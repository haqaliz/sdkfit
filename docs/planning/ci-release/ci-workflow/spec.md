# Spec: `ci-workflow` (T14)

- **Feature:** `ci-release`
- **PRD:** `docs/planning/ci-release/prd.md` (§ M1, M5)
- **Boundary:** `.github/workflows/ci.yml`, the README CI badge and the CI static tests.

## In-scope requirements

- `ci.yml` on `push`/`pull_request` to `master`; a `test` matrix `ubuntu-latest` × Python
  `3.11/3.12/3.13` with `astral-sh/setup-uv@v5`, `uv sync --frozen`, `uv run pytest`; a `build` job
  with `uv build` and `actions/upload-artifact@v4` (name `dist`, path `dist/`); concurrency cancels
  superseded runs.
- README: a CI status badge linking the workflow.
- `tests/test_ci.py`: parse the YAML and assert the triggers, matrix, the setup/build/pytest steps
  and the artifact. Offline.

## Out-of-scope

- The release workflow/PyPI/docs; macOS runners; code/config changes.

## Acceptance criteria

- **AC1 — Triggers.** `push` and `pull_request` on `master`.
- **AC2 — Test job.** Ubuntu 3.11–3.13; `uv sync --frozen`; `uv run pytest`.
- **AC3 — Build job.** `uv build`; upload `dist/`.
- **AC4 — Badge.** The README links the CI workflow badge.
- **AC5 — Tests.** The static invariants pass; the PR's CI run is the integration check.
