# Card: release/v0.3.0

- **Source:** FALLBACK — no GitHub issue (`gh issue list` is empty).
- **Owner:** aliz
- **Type:** release
- **Capability:** **Release/consolidation** — v0.3.0
- **Milestone:** after T12e; the third tagged release
- **Branch:** `release/v0.3.0/aliz`
- **Worktree:** `.claude/worktrees/release-v0.3.0`

## Brief

Since v0.2.0 the repo shipped cross-file receiver inference (T12e) and the CI/tag release pipeline.
This release moves T12e from `Unreleased` into `0.3.0`, bumps the package, runs the local release
check, and publishes the annotated `v0.3.0` tag. The tag exercises the new release workflow for the
first time: tests, wheel/sdist assets and the changelog body; the PyPI job stays skipped (gate off).

No new runtime behavior; no PyPI publication; the service stays self-hosted.

## Scope fence

Not this card: new features, cross-package indexes, a hardened cloud deployment.
