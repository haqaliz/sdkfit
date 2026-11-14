# Spec: `release-workflow` (T14)

- **Feature:** `ci-release`
- **PRD:** `docs/planning/ci-release/prd.md` (§ M2–M5)
- **Boundary:** `.github/workflows/release.yml`, the PyPI job, `docs/RELEASE.md` and the release
  static tests.

## In-scope requirements

- `release.yml` on tags `v*`: a `build` job (tests, `uv build`, upload `dist`); a `release` job
  (`contents: write`) downloading `dist`, extracting `## [<version>]` from `CHANGELOG.md` into a
  non-empty `release-notes.md`, and `softprops/action-gh-release@v2` with `body_path`,
  `files: dist/*`, `fail_on_unmatched_files`.
- A `publish` job (`needs: build`, `if: vars.PYPI_PUBLISH == 'true'`, `environment: pypi`,
  `id-token: write`, `contents: read`) downloading `dist` and
  `pypa/gh-action-pypi-publish@release/v1` with `password: ${{ secrets.PYPI_API_TOKEN }}`.
- `docs/RELEASE.md`: the PR/CI flow, the tag-triggered release, the `PYPI_PUBLISH`/`PYPI_API_TOKEN`/
  `pypi` environment setup, the local pre-tag `scripts/release_check.sh`, the manual fallback.
- `tests/test_ci.py`: parse the YAML and assert the tag trigger, jobs, permissions, the release
  action/body/files, the PyPI gate/secret, the docs keys. Offline.

## Out-of-scope

- The CI workflow/badge; trusted publishing (OIDC); signing/attestations.

## Acceptance criteria

- **AC1 — Trigger.** Tags `v*` only.
- **AC2 — Release.** `contents: write`; the changelog body; the wheel/sdist files.
- **AC3 — PyPI.** Gated by `vars.PYPI_PUBLISH`; the `pypi` environment; the `PYPI_API_TOKEN` secret;
  skipped by default.
- **AC4 — Docs.** The flow and the operator setup are documented.
- **AC5 — Tests.** The static invariants pass; the next tag exercises the workflow.
