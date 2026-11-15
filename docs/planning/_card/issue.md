# Card: release/v0.4.0

- **Source:** FALLBACK — no GitHub issue (`gh issue list` is empty).
- **Owner:** aliz
- **Type:** release
- **Capability:** **Release/consolidation** — v0.4.0
- **Milestone:** after T15; the fourth tagged release
- **Branch:** `release/v0.4.0/aliz`
- **Worktree:** `.claude/worktrees/release-v0.4.0`

## Brief

Since v0.3.0 the repo shipped the hardened cloud deployment (T15): a Postgres run store/queue,
`--database-url`, Kubernetes manifests and the cloud guide. This release moves T15 from
`Unreleased` into `0.4.0`, bumps the package, runs the local release check, and publishes the
annotated `v0.4.0` tag. The tag workflow creates the GitHub release with the wheel/sdist and the
changelog body; the PyPI job stays skipped (gate off).

No new runtime behavior beyond T15; no PyPI publication; the service stays self-hosted.

## Scope fence

Not this card: new features, repo-wide inference, a published container image, managed-DB IaC.
