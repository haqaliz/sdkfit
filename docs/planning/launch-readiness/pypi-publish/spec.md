# Spec: `pypi-publish` (T16)

- **Feature:** `launch-readiness`
- **PRD:** `docs/planning/launch-readiness/prd.md` (§ M1, M5)
- **Boundary:** the PyPI trusted-publishing job, the release guide and the static workflow tests.

## In-scope requirements

- `release.yml` `publish`: keep `needs: build`, `if: vars.PYPI_PUBLISH == 'true'`,
  `environment: pypi`, `id-token: write`, `contents: read`; drop the `PYPI_API_TOKEN` password and
  let `pypa/gh-action-pypi-publish@release/v1` use OIDC (`packages-dir: dist/`).
- `docs/RELEASE.md`: replace the token setup with the PyPI trusted-publisher setup (owner, repo,
  workflow `release.yml`, environment `pypi`), the gate, the immutability warning and a
  `pip install tenonhq` smoke test.
- `tests/test_ci.py`: assert OIDC (no password, no token secret, `id-token: write`, the environment,
  the gate), and the guide has no token instructions.
- No other workflow/behavior change.

## Out-of-scope

- TestPyPI, API tokens, the GitHub release assets (unchanged), the image job.

## Acceptance criteria

- **AC1 — OIDC.** The publish job has no password/token; `id-token: write`; `environment: pypi`;
  the action is `pypa/gh-action-pypi-publish@release/v1`.
- **AC2 — Gate.** The job is skipped unless `vars.PYPI_PUBLISH == 'true'`.
- **AC3 — Docs.** The guide explains the one-time trusted-publisher setup and the install check, and
  contains no `PYPI_API_TOKEN`.
- **AC4 — Regression.** The static tests and the full suite pass.
