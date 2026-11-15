# Spec: `image-publish` (T16)

- **Feature:** `launch-readiness`
- **PRD:** `docs/planning/launch-readiness/prd.md` (§ M2, M5)
- **Boundary:** the GHCR image job, the image references, the cloud guide and the static tests.

## In-scope requirements

- `release.yml` `image` job: `needs: build`, `contents: read`, `packages: write`; a version step
  (`${GITHUB_REF_NAME#v}`), a lowercased image name (`ghcr.io/${GITHUB_REPOSITORY,,}`),
  `docker/login-action@v3` with `GITHUB_TOKEN`, and `docker/build-push-action@v6` pushing
  `<image>:<version>` and `<image>:latest`.
- `deploy/k8s/deployment.yaml`: the image is `ghcr.io/haqaliz/tenon:latest` with a comment to pin a
  release tag; `docs/technical/CLOUD.md` says the tag workflow publishes the image, keeps the
  build-your-own fallback and notes the package may start private.
- `tests/test_ci.py`: the job, permissions, login/build actions and both tags.
- No Dockerfile behavior change.

## Out-of-scope

- A registry other than GHCR, multi-arch builds, signing/attestations, publishing on non-tag
  branches.

## Acceptance criteria

- **AC1 — Job.** The image job needs `build`, has `packages: write`, logs in to `ghcr.io` and uses
  `docker/build-push-action`.
- **AC2 — Tags.** It pushes `ghcr.io/<repo>:<version>` and `:latest`.
- **AC3 — References.** The manifest and guide use the published image; the note about visibility
  and the manual fallback remain.
- **AC4 — Regression/Tests.** Static invariants and the full suite pass.
