# Card: feat/launch-readiness

- **Source:** FALLBACK — no GitHub issue (`gh issue list` is empty).
- **Owner:** aliz
- **Type:** feat (launch engineering + docs)
- **Capability:** **Product Hunt launch readiness** — the last mile between a shipped roadmap and a
  public launch
- **Milestone:** after v0.4.0
- **Branch:** `feat/launch-readiness/aliz`
- **Worktree:** `.claude/worktrees/feat-launch-readiness`

## Brief

T1–T15 are shipped and v0.4.0 is tagged, but a launch would currently point people at an install
that does not exist (`pip install tenonhq` is gated off) and a container image that was never
published (`ghcr.io/haqaliz/tenon:0.4.0`). There is also no public demo and no launch copy.

This slice makes the project **launch-ready**, not the launch itself:
- **PyPI:** switch the gated publish job to trusted publishing (OIDC), add a TestPyPI dry-run path,
  and prove the install (`pip install tenonhq` → `tenon --version`).
- **Container image:** build and push `ghcr.io/haqaliz/tenon` on a `v*` tag, so the Kubernetes
  manifests reference a real image.
- **Demo:** a deterministic, offline launch demo (a consumer repo + a vendor change + a bundle) with
  a script that shows `tenon check` and `tenon fix` output an audience can read.
- **Launch kit:** positioning, tagline, short/long description, FAQ, first-comment draft, gallery
  plan, launch-day checklist, and a name/handles risk check.
- **Docs/tests:** the release guide, README launch link, static workflow tests.

No new locator/provider/service capability. The actual Product Hunt submission, domain, and hosted
demo stay out of scope.

## External dependencies (user-side, documented)

- A PyPI account and the `tenonhq` project with a trusted publisher for this repo/workflow; a
  TestPyPI project for the dry run.
- GitHub repo permission to publish packages; make the GHCR package public after the first push.
- The launch itself: maker account, assets, schedule.
