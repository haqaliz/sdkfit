# PRD: Launch readiness (T16)

- **Slug:** `launch-readiness`
- **Capability:** **T16 Launch readiness** — the last mile between a shipped roadmap and a public
  Product Hunt launch
- **Milestone:** after v0.4.0
- **Status:** draft for review
- **Card:** `docs/planning/_card/issue.md`

## Problem Statement

T1–T15 are shipped and v0.4.0 is tagged, but the project is not launch-ready:

- `pip install tenonhq` does not work: the PyPI job is gated off and token-based, and has never run.
- The Kubernetes manifests point at `ghcr.io/haqaliz/tenon:0.4.0`, but no workflow publishes an image.
- There is no public, reproducible demo of the core value: a vendor changes an API, Tenon finds the
  affected call sites, rewrites them, proves the tests and opens the PR.
- There is no launch copy, FAQ, gallery plan or checklist, and no check for the `tenon` name.

T16 makes the project **launch-ready** — it does not submit the launch. The first real PyPI and GHCR
publishes happen on the next tag after the user configures the PyPI trusted publisher; the Product
Hunt submission, a hosted demo and paid plans stay out of scope.

**For whom:** the maker preparing a launch, the first installers, and the providers evaluating
whether to run Tenon.

## Goals & Success Metrics

1. **One install command.** A tag release publishes `tenonhq` to PyPI via trusted publishing (no
   token secret), still behind an explicit `PYPI_PUBLISH` gate; the docs prove
   `pip install tenonhq` → `tenon --version`.
2. **One pullable image.** A tag release builds and pushes
   `ghcr.io/<owner>/<repo>:<version>` and `:latest`, so the Kubernetes guide references a real image.
3. **One honest demo.** An offline, deterministic demo (consumer repo + vendor change + bundle +
   script + transcript) shows `tenon check` finding the site and `tenon fix` proving the change.
4. **One launch kit.** Positioning, tagline, short/long description, who it is for, FAQ, first
   comment, gallery plan, launch-day checklist and a name/handles risk check.
5. **Tests/docs.** Static workflow invariants, a demo integration test, the release guide, README/
   CHANGELOG/roadmap updates; all prior tests green.

## Requirements

### Must have

- **M1 — PyPI trusted publishing.** `.github/workflows/release.yml` replaces the
  `PYPI_API_TOKEN` password with OIDC (`id-token: write`, `environment: pypi`,
  `pypa/gh-action-pypi-publish@release/v1` with no password), still gated by
  `vars.PYPI_PUBLISH == 'true'`. `docs/RELEASE.md` documents the PyPI project (`tenonhq`), the
  trusted-publisher fields (owner, repo, workflow `release.yml`, environment `pypi`), and a
  `pip install tenonhq` smoke test. No token secret anywhere.
- **M2 — GHCR image.** A `image` job in `release.yml` (`needs: build`, `packages: write`,
  `contents: read`) logs in with `GITHUB_TOKEN`, builds the repo `Dockerfile` and pushes
  `ghcr.io/${{ github.repository }}:<version>` plus `:latest`; the version strips the `v`. The
  cloud guide uses the published image and keeps a "build your own" fallback; the guide notes the
  package must be made public after the first push.
- **M3 — Launch demo.** `examples/launch-demo/` with a small consumer package, the vendor's old/new
  OpenAPI specs, a provider bundle and a README telling the story. `scripts/launch_demo.sh` copies
  the demo to a temp dir, runs `tenon check` (exit 1, names the site) and `tenon fix` (exit 0, proof
  passes), and prints a readable transcript; `docs/launch/DEMO.md` records the exact output. No
  network and no writes into the checkout.
- **M4 — Launch kit.** `docs/launch/` with:
  - `LAUNCH.md`: positioning, three tagline options, short (60 chars) and long descriptions, who it
    is for, the problem/solution, differentiators, what not to claim, and the launch-day checklist.
  - `FAQ.md`: the questions a first installer asks (is it a SaaS? does it push to my repo? which
    languages? does it need an LLM? what does it cost? how do I self-host?).
  - `GALLERY.md`: the images the Product Hunt page needs, with captions and the exact screens to
    capture (no generated art in this slice).
  - `NAME_CHECK.md`: the `tenon` name, PyPI/npm/GitHub handles and known conflicts, with a
    recommendation and residual risk.
  - `FIRST_COMMENT.md`: the maker's first comment.
- **M5 — Tests/docs.** `tests/test_launch.py` statically checks the PyPI OIDC job (no token,
  `id-token: write`, `environment: pypi`, gate), the GHCR job (`packages: write`,
  `docker/build-push-action`, a `ghcr.io` tag), the demo script (runs check/fix offline and writes
  nothing into the checkout), and the launch-kit keys. Update `docs/RELEASE.md`, README (launch
  status/install path once published), `CHANGELOG.md` `Unreleased`, `CAPABILITY_ROADMAP.md` (T16) and
  the status surfaces.
- **M6 — No capability change.** No locator/provider/service behavior; no new runtime dependency;
  version stays 0.4.0 with an `Unreleased` entry.

### Should have

- **S1 — Least privilege.** `packages: write` only on the image job, `id-token: write` only on
  publish, `contents: read` by default.
- **S2 — No irreversible surprise.** The PyPI job stays skipped unless `PYPI_PUBLISH=true`; the docs
  say a PyPI version cannot be reused, so the first publish is a deliberate act.
- **S3 — Honest copy.** No invented benchmarks, customers or hosted-service claims; the kit states
  self-hosted, single-tenant and pre-1.0.

### Nice to have

- **N1 — TestPyPI dry run**; not chosen.
- **N2 — Generated launch visuals**; not in this slice.
- **N3 — A hosted demo/domain**; out of scope.

## Data Model / API

No runtime data. Workflow jobs, a demo directory/script, and launch docs.

## Technical Considerations

- **Why trusted publishing.** No long-lived PyPI token to store or rotate; the job proves the
  repository identity via OIDC. The project/environment still needs one-time setup on PyPI.
- **Why the gate stays.** Publishing is irreversible and public; the variable keeps a tag from
  publishing until the operator opts in.
- **Why GHCR with `GITHUB_TOKEN`.** No new secret; the repo token can push packages with
  `packages: write`, and the package is linked to the repo.
- **Why the demo reuses the shipped pipeline.** The demo runs `tenon check`/`tenon fix` on real
  fixtures, not a staged animation; the transcript is the evidence.
- **Why the name check is explicit.** A launch under a conflicting name wastes the one launch; the
  check is cheap and the risk is documented.

## Risks & Open Questions

- **First live publish.** The PyPI/GHCR jobs are only exercised on the next tag; PyPI project and
  trusted-publisher setup are user-side. A misconfiguration fails the job, not the GitHub release
  assets (they are a separate job).
- **Version 0.4.0 already exists as a GitHub release.** The first PyPI version should be the next tag
  (`v0.5.0`); PyPI cannot republish 0.4.0 later.
- **GHCR visibility.** A package created by `GITHUB_TOKEN` may start private; the guide says to make
  it public for pullable manifests.
- **Name conflict.** `tenon` is a common word and may collide; the kit records findings instead of
  guessing.
- **Launch copy accuracy.** The kit lists what not to claim (no SaaS, no hosted demo, no customer
  logos, no benchmark beyond the repo's own).
- **Open question — should the publish job run for a pre-release tag?** No; `v*` tags are stable
  releases, as today.

## Out of Scope

- The actual Product Hunt submission, scheduling, gallery art, a hosted demo/domain.
- TestPyPI, PyPI tokens, paid plans/billing, a marketing site.
- New locator/provider/service behavior.

## Aspect Proposals (for `tech-plan`)

| Aspect | Boundary |
|---|---|
| `pypi-publish` | The trusted-publishing job, the release guide, the static workflow test. |
| `image-publish` | The GHCR job, the image tags, the cloud-guide fallback, the static test. |
| `launch-demo` | `examples/launch-demo/`, `scripts/launch_demo.sh`, the transcript and its test. |
| `launch-kit` | `docs/launch/*`, the name check, README/CHANGELOG/roadmap/status. |

## Self-critique (prd-generator pass)

| Dimension | Rating | Note |
|---|---|---|
| Problem definition | 🟢 | Install and image paths are broken for a launch; no demo/copy. |
| User understanding | 🟢 | Maker, first installer, evaluating provider; the flows are concrete. |
| Success metrics | 🟢 | Install, pull, demo, kit, tests. |
| Scope clarity | 🟢 | Readiness only; no submission, hosted demo or art. |
| Edge cases & risks | 🟡 | First-publish and name risks are real; gated and documented. |
| Stakeholder alignment | 🟡 | Solo project; the review gate is the approver. |
| Feasibility | 🟢 | Standard GitHub Actions and existing fixtures; no dependency. |
| Go-to-market | 🟢 | Turns shipped work into an installable, explainable launch. |

**Areas to strengthen before sharing:** the live publishes cannot be proven locally; the first tag
after setup is the integration test. The copy must stay honest about the self-hosted, single-tenant
model.

**The question I would want answered before greenlighting this:** *If I launch tomorrow, can a
visitor install and run it?* After T16, yes — provided the one-time PyPI trusted-publisher setup is
done and the next tag has published.
