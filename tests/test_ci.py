"""Static invariants for the CI and release workflows."""

import os
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"


def a_workflow(name: str) -> dict:
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))


def a_step(steps: list, prefix: str) -> dict:
    return next(step for step in steps if str(step.get("uses", "")).startswith(prefix))


# Spec AC1/AC2/AC3: CI runs the suite on the matrix and builds/upload the artifacts.
def test_ci_runs_the_suite_and_builds_artifacts():
    workflow = a_workflow("ci.yml")

    assert "push" in workflow["on"]
    assert "pull_request" in workflow["on"]

    jobs = workflow["jobs"]
    test = jobs["test"]
    assert test["runs-on"] == "ubuntu-latest"
    assert test["strategy"]["matrix"]["python-version"] == [
        "3.11",
        "3.12",
        "3.13",
    ]
    a_step(test["steps"], "astral-sh/setup-uv@")
    runs = [step.get("run") for step in test["steps"]]
    assert "uv sync --frozen" in runs
    assert "uv run pytest" in runs

    build = jobs["build"]
    runs = [step.get("run") for step in build["steps"]]
    assert "uv sync --frozen" in runs
    assert "uv build" in runs
    upload = a_step(build["steps"], "actions/upload-artifact@")
    assert upload["with"]["path"] == "dist/"
    assert upload["with"]["name"] == "dist"


# Spec AC1/AC2/AC3: a tag builds, creates the release with assets and changelog notes.
def test_release_is_tag_driven_with_assets_and_notes():
    workflow = a_workflow("release.yml")

    assert workflow["on"]["push"]["tags"] == ["v*"]

    jobs = workflow["jobs"]
    assert {"build", "release", "publish"} <= set(jobs)
    release = jobs["release"]
    assert release["permissions"]["contents"] == "write"
    runs = "\n".join(str(step.get("run", "")) for step in release["steps"])
    assert "CHANGELOG.md" in runs
    assert "release-notes.md" in runs
    action = a_step(release["steps"], "softprops/action-gh-release@")
    assert action["with"]["files"] == "dist/*"
    assert action["with"]["body_path"] == "release-notes.md"
    assert action["with"]["fail_on_unmatched_files"] is True


# Spec AC2: the release body is the version's section, including the dated heading.
def test_the_release_notes_extraction_handles_the_dated_heading(tmp_path):
    workflow = a_workflow("release.yml")
    release = workflow["jobs"]["release"]
    script = next(
        step["run"]
        for step in release["steps"]
        if "release-notes.md" in str(step.get("run", ""))
    )
    (tmp_path / "CHANGELOG.md").write_text(
        "## [Unreleased]\n\n"
        "## [1.2.3] - 2026-01-01\n\n"
        "### Added\n\n"
        "- the feature\n\n"
        "## [1.2.2] - 2025-12-01\n\n"
        "- the old entry\n",
        encoding="utf-8",
    )

    subprocess.run(
        ["bash", "-e", "-c", script],
        cwd=tmp_path,
        env={**os.environ, "GITHUB_REF_NAME": "v1.2.3"},
        check=True,
    )

    notes = (tmp_path / "release-notes.md").read_text(encoding="utf-8")
    assert "the feature" in notes
    assert "the old entry" not in notes


# Spec AC2/AC5: a tag builds and pushes the service image to GHCR.
def test_the_image_job_publishes_to_ghcr():
    image = a_workflow("release.yml")["jobs"]["image"]

    assert image["needs"] == "build"
    assert image["permissions"]["packages"] == "write"
    assert image["permissions"]["contents"] == "read"
    a_step(image["steps"], "docker/login-action@")
    build = a_step(image["steps"], "docker/build-push-action@")
    assert build["with"]["push"] is True
    assert "ghcr.io/" in build["with"]["tags"]
    assert ":latest" in build["with"]["tags"]
    runs = "\n".join(str(step.get("run", "")) for step in image["steps"])
    assert "GITHUB_REF_NAME#v" in runs


# Spec AC3: PyPI uses trusted publishing, still gated and skipped by default.
def test_publish_uses_trusted_publishing_and_is_gated():
    publish = a_workflow("release.yml")["jobs"]["publish"]

    assert "PYPI_PUBLISH" in publish["if"]
    assert publish["environment"] == "pypi"
    assert publish["permissions"]["id-token"] == "write"
    assert publish["permissions"]["contents"] == "read"
    action = a_step(publish["steps"], "pypa/gh-action-pypi-publish@")
    assert "password" not in action.get("with", {})
    assert action["with"]["packages-dir"] == "dist/"
    workflow = (WORKFLOWS / "release.yml").read_text(encoding="utf-8")
    assert "PYPI_API_TOKEN" not in workflow


# Spec AC4: the badge and the operator guide carry the workflow names and settings.
def test_the_badge_and_guide_document_the_pipeline():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "actions/workflows/ci.yml/badge.svg" in readme
    guide = (ROOT / "docs" / "RELEASE.md").read_text(encoding="utf-8")
    for value in (
        "ci.yml",
        "release.yml",
        "PYPI_PUBLISH",
        "trusted publisher",
        "pypi",
        "pip install tenonhq",
    ):
        assert value in guide
    assert "PYPI_API_TOKEN" not in guide
