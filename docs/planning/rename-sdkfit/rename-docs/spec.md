# Spec: `rename-docs` (T17)

- **Feature:** `rename-sdkfit`
- **PRD:** `docs/planning/rename-sdkfit/prd.md` (§ M4, M5)
- **Boundary:** README/VISION/CLAUDE/current technical docs, the launch kit/name check and the
  changelog/status surfaces.

## In-scope requirements

- README title/tagline/install/links/badges; a short "formerly Tenon" only in historical records, not
  the shipped docs (the invariant keeps the old name out).
- `VISION.md`/`CLAUDE.md` name and origin paragraphs; `docs/ROADMAP.md`,
  `docs/technical/{ARCHITECTURE,CAPABILITY_ROADMAP,CLOUD,DEPLOYMENT}.md`, `docs/RELEASE.md` current
  names.
- Launch kit: SDK Fit in `LAUNCH.md`, `FAQ.md`, `GALLERY.md`, `FIRST_COMMENT.md`, `DEMO.md`; rewrite
  `NAME_CHECK.md` with the chosen-name evidence and the old Tenon/tenonhq collision as history.
- `CHANGELOG.md`: a new `Unreleased` "Changed — renamed to SDK Fit" entry; historical entries stay.
- `docs/planning/**` stay as written.
- Tests: the kit/demo invariants updated; the rename invariant covers the docs.

## Out-of-scope

- Code/ops (the other aspects), generated art, the submission.

## Acceptance criteria

- **AC1 — Current docs.** A reader sees SDK Fit/`sdkfit` everywhere, with `sdkfit.dev` and the
  install path.
- **AC2 — Name check.** `NAME_CHECK.md` records the chosen name's live availability and the old
  collision; no unresolved blocker remains.
- **AC3 — History.** The changelog preserves Tenon releases and adds the rename entry; the full
  suite passes.
