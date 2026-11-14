# Card: feat/ci-release

- **Source:** FALLBACK — no GitHub issue (`gh issue list` is empty).
- **Owner:** aliz
- **Type:** feat
- **Capability:** **CI/PyPI release pipeline** — the release-operations follow-up to v0.2.0
- **Milestone:** after v0.2.0
- **Branch:** `feat/ci-release/aliz`
- **Worktree:** `.claude/worktrees/feat-ci-release`

## Brief

Every release is manual: run the tests, `uv build`, install the wheel, tag, and `gh release create`.
The tests run only locally; a pull request has no CI.

This slice adds:
- a **CI workflow** on push/PR: the suite on a Python matrix, plus a wheel/sdist build artifact;
- a **release workflow** on a `v*` tag: re-run the tests, build, attach the wheel/sdist to the GitHub
  release with the changelog section as the body;
- an **optional PyPI publish** (token or trusted publishing) gated so a release never publishes by
  accident;
- docs (`docs/RELEASE.md`, README CI badge) and static workflow tests; the workflows run for real on
  the PR/next tag.

No runtime/locator/provider behavior changes.

## Constraints carried in from the repo

- `pyproject.toml`/`uv.lock`; the `uv` toolchain; Python >= 3.11.
- The release checklist and `scripts/release_check.sh` are the current manual path.
- The repo is `haqaliz/tenon`; the package/distribution is `tenonhq`.
- No secrets in the repo; the PyPI token (if chosen) is a GitHub secret, the publish gate a
  repository variable/environment.

## Scope fence

Not this card: new features, cross-file inference, a hardened cloud deployment, a SaaS control
plane, signing/provenance beyond the PyPI defaults.
