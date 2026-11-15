# PRD: Rename to SDK Fit (T17)

- **Slug:** `rename-sdkfit`
- **Capability:** **T17 Rename to SDK Fit** — resolve the launch-name blocker
- **Milestone:** after T16
- **Status:** draft for review
- **Card:** `docs/planning/_card/issue.md`

## Problem Statement

The T16 launch-name check found that **Tenon** and the PyPI distribution **`tenonhq`** collide with
the active company at **tenonhq.com**. The chosen launch name is **SDK Fit**, distribution and CLI
**`sdkfit`**. The repository still says Tenon everywhere: package, import, CLI, env vars, Docker,
Kubernetes, docs and the launch kit. Launching under SDK Fit while shipping a `tenon` command and a
`tenonhq` install would be incoherent and preserve the collision.

## Goals & Success Metrics

1. **One name.** `pip install sdkfit`, `sdkfit --version`, `import sdkfit`, `SDKFIT_*` env vars,
   `ghcr.io/.../sdkfit`, and SDK Fit in the docs/launch kit.
2. **No stale surface.** No user-facing `tenon`/`tenonhq`/`TENON_` reference remains outside
   historical changelog/planning records.
3. **Same behavior.** All 2,775 tests pass; the demo, CLI and service work unchanged.
4. **A clean launch release.** The next release is v0.5.0 under `sdkfit`; the PyPI trusted-publisher
   guide names `sdkfit`.

## Requirements

### Must have

- **M1 — Package/CLI/module.** `pyproject.toml` `name = "sdkfit"`, script `sdkfit`, `src/tenon` →
  `src/sdkfit`, all imports, argparse `prog`, `--version` output `sdkfit <version>`, `_serve_command`
  child import, docstrings/messages.
- **M2 — Config.** Rename `TENON_API_TOKEN`, `TENON_WEBHOOK_SECRET`, `TENON_DATABASE_URL`,
  `TENON_APP_ID`, `TENON_APP_INSTALLATION_ID` and any `TENON_*` env to `SDKFIT_*`; update tests,
  Compose, Kubernetes and docs. No `tenon` compatibility alias (no public PyPI release yet).
- **M3 — Ops.** Dockerfile entrypoint/healthcheck, Compose service/volume names, Caddy comment,
  Kubernetes resource/label/secret/PVC/DB names and image path, scripts (`release_check.sh`,
  `launch_demo.sh`), workflows/guides that name the distribution or repo.
- **M4 — Docs.** README title/tagline/install/links, VISION/CLAUDE, current technical docs, the
  launch kit (including a rewritten `NAME_CHECK.md` that records the chosen name, its availability
  and the old collision), a `CHANGELOG.md` `Unreleased` entry. Keep historical changelog entries and
  `docs/planning/**` as written.
- **M5 — Tests.** Update imports/expected strings/fixtures/env names; add/adjust a rename invariant
  test: no `tenon`/`TENON_` in the shipped package, CLI, Dockerfile, K8s, scripts or launch kit
  (excluding the historical changelog/planning). Full suite green; the demo and a built image pass.
- **M6 — Repo (decision).** Optionally rename the GitHub repository `haqaliz/tenon` →
  `haqaliz/sdkfit` (old URLs redirect; the GHCR path becomes `ghcr.io/haqaliz/sdkfit`); otherwise the
  product name changes but the repo URL stays.

### Should have

- **S1 — One commit per surface** (code, ops, docs) for reviewability.
- **S2 — No version bump.** The rename PR keeps 0.4.0; the release PR cuts 0.5.0.
- **S3 — Search-audit.** A final `grep` over the shipped surfaces; the test guards it.

### Nice to have

- **N1 — Logo/visual identity**; not in this slice.
- **N2 — Redirect/alias for the old command**; rejected (pre-1.0, no external installs).

## Data Model / API

No data/API shape change. Public names change: distribution, CLI, import package, env vars, image,
repo/links.

## Technical Considerations

- **Why a full rename.** A half-rename leaves the collision in the install line and the command, the
  first things a launch visitor sees.
- **Why no alias.** v0.4.0 was never published to PyPI; there are no external installs to preserve.
  An alias would keep the old brand in the package.
- **Why keep old changelog/planning records.** They are history; rewriting them would misstate what
  shipped under the Tenon name. The README can say "formerly Tenon" once.
- **Why the repo rename is optional.** It is an external, visible action; GitHub redirects old URLs,
  but the maintainer should approve it.

## Risks & Open Questions

- **Missed references.** 330 files mention the old name; the rename is mechanical but wide. The
  invariant test and a `grep` audit guard the shipped surfaces; historical files are exempt.
- **Repo rename.** Changing the repo changes the GHCR path and all links; old URLs redirect. The
  local remote and worktree paths need updating.
- **Old release assets.** v0.1.0–v0.4.0 releases and tags keep the Tenon name and URLs; that is
  expected.
- **Name check.** `sdkfit.com` is registered but has no site; `sdkfit.dev` is free, and PyPI/npm/
  GitHub/Product Hunt are clear. Document the `.com` caveat.
- **Open question — rename the GitHub repo too?** Recommended, pending approval.

## Out of Scope

- Behavior changes, a version bump, the PyPI/GHCR live publish, visuals/submission.
- Rewriting historical changelog entries or planning records.

## Aspect Proposals (for `tech-plan`)

| Aspect | Boundary |
|---|---|
| `rename-code` | Package/CLI/module/env names, source, tests, the invariant test. |
| `rename-ops` | Docker, Compose, Caddy, Kubernetes, scripts, workflows/guides. |
| `rename-docs` | README/VISION/CLAUDE/technical docs, launch kit/name check, changelog/status. |

## Self-critique (prd-generator pass)

| Dimension | Rating | Note |
|---|---|---|
| Problem definition | 🟢 | The collision is real and the old name is everywhere. |
| User understanding | 🟢 | First installer sees `pip install sdkfit` and `sdkfit`. |
| Success metrics | 🟢 | One name, no stale shipped surface, same behavior, clean release. |
| Scope clarity | 🟢 | Rename only; history and version bump excluded. |
| Edge cases & risks | 🟡 | Wide mechanical change and the repo rename are the risks; tests/audit cover them. |
| Stakeholder alignment | 🟡 | Solo project; the review gate is the approver. |
| Feasibility | 🟢 | Mechanical rename over a green suite; no dependency. |
| Go-to-market | 🟢 | Removes the launch blocker and gives a coherent brand. |

**Areas to strengthen before sharing:** the rename must not leave a single user-facing `tenon`; the
invariant test is the guard.

**The question I would want answered before greenlighting this:** *After the rename, can a visitor
install and run SDK Fit without seeing the old name?* Yes, except in the historical changelog and
planning records, which are intentionally preserved.
