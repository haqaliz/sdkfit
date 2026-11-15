# Releasing Tenon

Releases are tag-driven: a `v*` tag runs `.github/workflows/release.yml`, which tests, builds,
attaches the wheel/sdist to the GitHub release and optionally publishes to PyPI. The local checklist
below is the pre-tag check.

## Prerequisites

- `uv`, Python 3.11+, `git`, `gh` (for a manual fallback), and a clean `master`.
- The version in `pyproject.toml` (and `uv.lock`) is the release version; `CHANGELOG.md` has the
  `## [x.y.z] - YYYY-MM-DD` section.

## CI

`.github/workflows/ci.yml` runs on every push/PR to `master`: the suite on Ubuntu with Python
3.11/3.12/3.13 (`uv sync --frozen` + `uv run pytest`) and a build job that uploads the `dist/`
artifact. The PR must be green before merging.

## Local pre-tag check

1. **Full suite (offline).**

   ```sh
   uv sync --frozen
   uv run pytest
   ```

2. **Version.** The source run shows the installed metadata; re-sync after a bump.

   ```sh
   uv sync
   uv run tenon --version
   ```

3. **Changelog.** The release body is the `## [x.y.z]` section; review the shipped capabilities and
   the known limits.

4. **Build and clean-install smoke.**

   ```sh
   uv build
   tmp=$(mktemp -d)
   uv venv "$tmp/venv"
   uv pip install --python "$tmp/venv/bin/python" --quiet dist/tenonhq-*.whl
   "$tmp/venv/bin/tenon" --version
   "$tmp/venv/bin/tenon" check --help
   rm -rf "$tmp"
   ```

   `scripts/release_check.sh` runs the suite, build and smoke in one go.

5. **Merge the release PR** and update `master`.

   ```sh
   git checkout master
   git pull --ff-only origin master
   ```

## Tag and release

6. **Tag the merge commit** (annotated; push the tag). The tag starts the release workflow.

   ```sh
   git tag -a vX.Y.Z -m "Tenon vX.Y.Z"
   git push origin vX.Y.Z
   ```

7. **The release workflow.** `.github/workflows/release.yml` runs on the `v*` tag: it re-runs the
   tests, builds the wheel/sdist, extracts `## [x.y.z]` from `CHANGELOG.md` into the release body and
   creates/updates the GitHub release with `dist/*` attached. Watch it:

   ```sh
   gh run watch --workflow release.yml
   gh release view vX.Y.Z
   ```

8. **PyPI (optional).** The `publish` job uses **trusted publishing** (OIDC) and is skipped unless
   the `PYPI_PUBLISH` repository variable is `true`. One-time setup on PyPI:

   - The `tenonhq` project exists (create/reserve the name on your PyPI account).
   - Add a trusted publisher: owner `haqaliz`, repository `tenon`, workflow `release.yml`,
     environment `pypi`.
   - Create the `pypi` environment in GitHub (add reviewers if you want a manual approval).
   - Set the `PYPI_PUBLISH` repository variable to `true` only when you are ready to publish.

   There is **no API token secret**: the job proves the repository identity with a short-lived OIDC
   token. A PyPI version cannot be reused, so the first publish is deliberate; do not retag a
   published version.

   Verify the install after the workflow:

   ```sh
   pip install tenonhq==X.Y.Z
   tenon --version
   ```

9. **Verify** the release page/assets, the version badge, the changelog link, the container image
   (`ghcr.io/haqaliz/tenon:X.Y.Z`) and (if enabled) the PyPI version.

## Manual fallback

If the workflow is unavailable, the old path still works: push the tag and create the release
manually with the changelog section as the body, then upload the artifacts.

```sh
awk '/^## \[x.y.z\]/{flag=1; next} flag && /^## \[/{exit} flag' CHANGELOG.md > /tmp/tenon-notes.md
gh release create vX.Y.Z --title "vX.Y.Z" --notes-file /tmp/tenon-notes.md dist/*
```

## Notes

- Do not retag a published version; cut a patch for a fix.
- The tag/release happen after the PR merges, on `master`; the release PR carries the version,
  changelog and checklist.
- The workflows never echo a secret; PyPI publication uses OIDC trusted publishing, not a stored
  token.
