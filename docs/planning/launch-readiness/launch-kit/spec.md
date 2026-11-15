# Spec: `launch-kit` (T16)

- **Feature:** `launch-readiness`
- **PRD:** `docs/planning/launch-readiness/prd.md` (§ M4, M5)
- **Boundary:** `docs/launch/*` (except `DEMO.md`), the name/handles check and the
  README/CHANGELOG/roadmap/status surfaces.

## In-scope requirements

- `docs/launch/LAUNCH.md`: positioning, three tagline options, a short (≤60 char) and long
  description, who it is for, problem/solution, differentiators, what not to claim, the launch-day
  checklist and the exact install/verify commands.
- `docs/launch/FAQ.md`: at least whether it is a SaaS, whether it pushes to the user's repo, which
  languages, whether it needs an LLM, licensing/cost, self-hosting, and what happens on a failed
  mutation.
- `docs/launch/GALLERY.md`: four Product Hunt images with captions and the exact screens to
  capture; no generated art.
- `docs/launch/NAME_CHECK.md`: the `tenon` name, PyPI/npm/GitHub/PyPI-project status, known
  collisions (checked live) and a recommendation with residual risk.
- `docs/launch/FIRST_COMMENT.md`: the maker's first comment.
- `CHANGELOG.md` `Unreleased`, `CAPABILITY_ROADMAP.md` T16 row + "T16 as built", `ROADMAP.md`/
  `CLAUDE.md`/`ARCHITECTURE.md` status, and a pointer from `docs/RELEASE.md`.
- `tests/test_launch.py`: the kit files exist and the copy keys are present (no placeholder text,
  no invented metrics/customers).
- README: only claims that are true before the first PyPI publish (link the launch kit; do not
  claim `pip install` works until the tag publishes).

## Out-of-scope

- The submission, scheduling, generated visuals, a landing site, pricing.

## Acceptance criteria

- **AC1 — Copy.** The kit names the audience, problem, tagline, descriptions, FAQ, gallery and
  checklist; every claim matches the shipped features.
- **AC2 — Name.** The check records the live status and a recommendation; a material conflict is
  called out.
- **AC3 — Status.** Changelog/roadmap/status mention T16 and the install/publish state.
- **AC4 — Test/regression.** The kit invariants and the full suite pass.
