# Card: feat/rename-sdkfit

- **Source:** FALLBACK — no GitHub issue (`gh issue list` is empty).
- **Owner:** aliz
- **Type:** feat (rename/launch)
- **Capability:** **T17 Rename to SDK Fit** — resolve the launch-name blocker
- **Milestone:** after T16
- **Branch:** `feat/rename-sdkfit/aliz`
- **Worktree:** `.claude/worktrees/feat-rename-sdkfit`

## Brief

The T16 name check found that **Tenon**/`tenonhq` collides with the active company at
**tenonhq.com**. The launch name is now **SDK Fit**, distribution and CLI **`sdkfit`**.

This slice renames the product end to end:
- distribution, import package, console script, `--version`, env vars (`TENON_*` → `SDKFIT_*`);
- source/tests/fixtures, Dockerfile/Compose/Caddy, Kubernetes resource names and image path, scripts;
- README, current technical docs, launch kit, PyPI trusted-publisher guide, changelog/status;
- optionally the GitHub repository (`haqaliz/tenon` → `haqaliz/sdkfit`); GitHub redirects old URLs.

Historical `CHANGELOG.md` entries and `docs/planning/**` records keep the old name. No behavior change
and no version bump: the release PR will cut **v0.5.0** under the new name.

## Scope fence

Not this card: new features, a logo/visual identity, PyPI/GHCR live publishes, the Product Hunt
submission, backward-compatible `tenon` aliases (pre-1.0, no public PyPI release yet).
