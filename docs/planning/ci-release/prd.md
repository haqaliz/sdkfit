# PRD: CI and release pipeline (T14)

- **Slug:** `ci-release`
- **Capability:** **CI/PyPI release pipeline** — release-operations follow-up to v0.2.0
- **Milestone:** after v0.2.0
- **Status:** draft for review
- **Card:** `docs/planning/_card/issue.md`

## Problem Statement

Every release is manual: run the tests, `uv build`, install the wheel, tag, and `gh release create`.
A pull request has no CI, so a broken change is only found locally; release assets are copied by hand;
PyPI was never wired.

This slice adds:
- a **CI workflow** on push/PR: the suite on Ubuntu with Python 3.11–3.13, plus a wheel/sdist build
  artifact;
- a **release workflow** on a `v*` tag: re-run the tests, build, attach the wheel/sdist to the GitHub
  release with the version's changelog section as the body;
- an **optional PyPI publish** using a `PYPI_API_TOKEN` secret, gated by a `PYPI_PUBLISH` repository
  variable so a tag never publishes by accident;
- docs (README CI badge, `docs/RELEASE.md`) and static workflow tests. The workflows run for real on
  the PR (CI) and the next tag (release).

No runtime/locator/provider behavior changes.

**For whom:** the maintainer cutting releases, a contributor opening a PR, and an operator installing
from PyPI.

## Goals & Success Metrics

1. **CI on every PR/push.** The suite runs on Ubuntu 3.11–3.13; a build job produces a `dist/`
   artifact.
2. **Tag-driven release.** A `v*` tag runs tests/build and creates/updates the GitHub release with
   the wheel/sdist and the matching changelog section.
3. **Optional PyPI.** A `PYPI_PUBLISH=true` repository variable enables the publish job; otherwise
   the tag only cuts the GitHub release. The token is a secret, never in the repo.
4. **Docs/tests.** README CI badge, `docs/RELEASE.md` flow, static workflow invariants; the PR's CI
   check is the real integration test.
5. **No behavior change.** No code, config, or deployed-service change.

## Requirements

### Must have

- **M1 — CI.** `.github/workflows/ci.yml` on `push`/`pull_request` to `master`; a `test` matrix
  `ubuntu-latest` × Python `3.11/3.12/3.13` using `astral-sh/setup-uv@v5`, `uv sync --frozen`,
  `uv run pytest`; a `build` job `uv build` + `actions/upload-artifact@v4` (name `dist`, path
  `dist/`); concurrency cancels superseded runs.
- **M2 — Release.** `.github/workflows/release.yml` on tags `v*`; `contents: read` default; a `build`
  job (tests, `uv build`, upload `dist`); a `release` job (`contents: write`) that downloads `dist`,
  extracts `## [<version>]` from `CHANGELOG.md` into `release-notes.md` (non-empty), and uses
  `softprops/action-gh-release@v2` with `body_path`/`files: dist/*`/`fail_on_unmatched_files`.
- **M3 — PyPI.** A `publish` job (`needs: build`, `if: vars.PYPI_PUBLISH == 'true'`,
  `environment: pypi`, `id-token: write`, `contents: read`) downloading `dist` and running
  `pypa/gh-action-pypi-publish@release/v1` with `password: ${{ secrets.PYPI_API_TOKEN }}`.
- **M4 — Docs.** README CI badge; `docs/RELEASE.md` describing the PR/CI flow, the tag-triggered
  release, the `PYPI_PUBLISH`/`PYPI_API_TOKEN`/`pypi` environment setup, the local pre-tag
  `scripts/release_check.sh`, and the manual fallback.
- **M5 — Static tests.** `tests/test_ci.py` parses the YAML and asserts the triggers, jobs, matrix,
  the `uv run pytest`/`uv build` steps, the artifact, the release permissions/actions, the PyPI gate
  and secret, and the docs/badge. Offline.
- **M6 — No runtime change.** No source/config/service changes.

### Should have

- **S1 — Least privilege.** `contents: read` by default; `contents: write` only on the release job;
  `id-token: write` only on publish.
- **S2 — No secrets in the repo.** The token is a GitHub secret; workflows never echo it.
- **S3 — Deterministic artifacts.** `uv build` from the frozen lock; the tag version must match
  `pyproject.toml`/the changelog (the static test can assert the tag pattern and the changelog
  lookup, not the live tag).

### Nice to have

- **N1 — Trusted publishing (OIDC)** instead of the token; a later switch.
- **N2 — A release PR automation**; not needed.
- **N3 — Artifact attestations/signing**; the PyPI action's defaults only.

## Data Model / API

No runtime data. Two workflows and a static test.

## Technical Considerations

- **Why `uv`.** The repo's lock/toolchain is `uv`; the workflows use it for reproducible installs.
- **Why the matrix.** The declared `>=3.11` range is tested on the standard CI OS; if a dependency
  lacks a 3.11 wheel, the PR check surfaces it and the matrix is adjusted.
- **Why the tag workflow.** The release is already tag-driven; the workflow replaces the manual
  `gh release create` and attaches the exact artifacts.
- **Why the gate.** PyPI publication is irreversible (a version cannot be reused); an explicit
  variable is a deliberate opt-in.
- **Why static tests.** The YAML syntax is validated by GitHub on the PR; pytest checks the
  invariants without a runner.

## Risks & Open Questions

- **Workflow syntax.** The PR's CI run is the real test; the release workflow is exercised on the
  next tag. A local YAML parse catches shape, not runner behavior.
- **PyPI name.** The distribution is `tenonhq`; the token must be scoped to that project. A publish
  attempt without the project/token fails the job, not the release assets.
- **Tag/version drift.** The changelog extraction requires the `## [x.y.z]` section; a missing
  section fails the release job with an empty-notes test.
- **Re-tagging.** A re-pushed tag updates the release; PyPI rejects an existing version (expected).
- **Open question — should the CI matrix include macOS?** Not now; the standard runner is Ubuntu and
  the code targets POSIX. A macOS job is a later option.
- **Open question — should the publish job use trusted publishing?** The token is the chosen simple
  path; OIDC is a later switch.

## Out of Scope

- New features, cross-file inference, a hardened cloud deployment, a SaaS control plane.
- Signing/attestations beyond the PyPI action defaults; a docs site.

## Aspect Proposals (for `tech-plan`)

| Aspect | Boundary |
|---|---|
| `ci-workflow` | `ci.yml`, the README badge, the CI static tests. |
| `release-workflow` | `release.yml`, the PyPI job, `docs/RELEASE.md`, the release static tests. |

## Self-critique (prd-generator pass)

| Dimension | Rating | Note |
|---|---|---|
| Problem definition | 🟢 | No CI, manual assets, no PyPI. |
| User understanding | 🟢 | Maintainer/contributor/operator; the flows are concrete. |
| Success metrics | 🟢 | Matrix CI, tag release/assets, gated PyPI, docs, static tests. |
| Scope clarity | 🟢 | Workflows/docs only; no runtime change. |
| Edge cases & risks | 🟡 | Runner behavior only on GitHub, PyPI name/token and tag drift are real; documented/guarded. |
| Stakeholder alignment | 🟡 | Solo project; the review gate is the approver. |
| Feasibility | 🟢 | Standard GitHub Actions + `uv`/build actions; no new dependency. |
| Go-to-market | 🟢 | Repeatable releases and a PyPI install path. |

**Areas to strengthen before sharing:** the release workflow is only fully exercised on the next tag;
the PR validates CI and the YAML shape. The PyPI publication is an explicit operator opt-in.

**The question I would want answered before greenlighting this:** *If a tag is pushed, does anything
publish to PyPI by default?* The answer this card records: no; the publish job is skipped unless the
`PYPI_PUBLISH` variable is `true`, and the token is a secret.
