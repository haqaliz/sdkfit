"""Static invariants for the project site, brand assets and donations."""

from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
SITE = ROOT / "site"
NOWPAYMENTS = (
    "https://nowpayments.io/donation"
    "?api_key=52f38854-167a-4828-a00f-0424ab7dcc1e"
)


def a_step(steps: list, prefix: str) -> dict:
    return next(step for step in steps if str(step.get("uses", "")).startswith(prefix))


# Spec: the landing page carries the product, install path, links and donation.
def test_the_site_is_wired():
    html = (SITE / "index.html").read_text(encoding="utf-8")

    for value in (
        "SDK Fit",
        "Breaking API changes, fixed and proven.",
        "pip install sdkfit",
        "https://github.com/haqaliz/sdkfit",
        "https://pypi.org/project/sdkfit/",
        NOWPAYMENTS,
        "assets/sdkfit.svg",
        "assets/sdkfit-demo.png",
        "assets/sdkfit-proof.png",
        "assets/sdkfit-flow.png",
    ):
        assert value in html
    assert "<script" not in html


# Spec: the logo is the official mark, transparent and tightly cropped.
def test_the_logo_is_clean_and_branded():
    svg = (ROOT / "assets" / "sdkfit.svg").read_text(encoding="utf-8")

    assert "_Linear1" in svg
    assert "M1023.999,11.5" not in svg
    assert 'viewBox="350 195 330 370"' in svg


# Spec: the Pages workflow deploys only the site and the assets it references.
def test_the_pages_workflow_deploys_the_site():
    workflow = yaml.safe_load(
        (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
    )

    assert workflow["on"]["push"]["branches"] == ["master"]
    assert "workflow_dispatch" in workflow["on"]
    assert workflow["permissions"]["pages"] == "write"
    assert workflow["permissions"]["id-token"] == "write"
    deploy = workflow["jobs"]["deploy"]
    a_step(deploy["steps"], "actions/configure-pages@")
    a_step(deploy["steps"], "actions/upload-pages-artifact@")
    a_step(deploy["steps"], "actions/deploy-pages@")
    stage = next(step for step in deploy["steps"] if step.get("name") == "Stage site")
    for value in (
        "site/index.html",
        "assets/sdkfit.svg",
        "docs/launch/assets/check.png",
        "docs/launch/assets/fix.png",
        "docs/launch/assets/flow.png",
    ):
        assert value in stage["run"]


# Spec: the README shows the logo, links the site and offers the donation.
def test_the_readme_has_the_logo_site_and_donation():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "assets/sdkfit.svg" in readme
    assert "https://haqaliz.github.io/sdkfit/" in readme
    assert NOWPAYMENTS in readme


# Spec: the Product Hunt assets use the official logo.
def test_the_launch_assets_use_the_logo():
    for name in ("thumbnail", "check", "fix", "flow"):
        svg = (ROOT / "docs" / "launch" / "assets" / f"{name}.svg").read_text(
            encoding="utf-8"
        )
        assert "sdkfit.svg" in svg
