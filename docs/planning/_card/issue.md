# Card: release/v0.5.0

- **Source:** FALLBACK — no GitHub issue (`gh issue list` is empty).
- **Owner:** aliz
- **Type:** release
- **Capability:** **Launch release** — v0.5.0 under the SDK Fit name
- **Milestone:** after T17
- **Branch:** `release/v0.5.0/aliz`
- **Worktree:** `.claude/worktrees/release-v0.5.0`

## Brief

The first release under **SDK Fit** (`sdkfit`). It moves the T16 launch-readiness work and the T17
rename from `Unreleased` into `0.5.0`, bumps the package, and publishes the annotated `v0.5.0` tag.
The tag workflow creates the GitHub release with the wheel/sdist, publishes the
`ghcr.io/haqaliz/sdkfit` image, and publishes `sdkfit` to PyPI via OIDC trusted publishing
(`PYPI_PUBLISH=true`, `pypi` environment).

No behavior change; no new features; the service stays self-hosted.

## Scope fence

Not this card: new features, a Product Hunt submission, generated visuals, a hosted demo.
