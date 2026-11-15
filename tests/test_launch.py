"""Launch-readiness invariants: the offline demo and the launch kit."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
DEMO = ROOT / "examples" / "launch-demo"
BILLING = DEMO / "repo" / "acme" / "billing.py"


# Spec AC1/AC2/AC3: the demo runs check and fix offline and never writes the checkout.
def test_the_launch_demo_runs_check_and_fix():
    before = BILLING.read_text(encoding="utf-8")

    result = subprocess.run(
        ["bash", "scripts/launch_demo.sh"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )

    assert result.returncode == 0, result.stderr
    assert "1 certain site" in result.stdout
    assert "amount -> amount_cents" in result.stdout
    assert "Proof: TESTS_PASSED" in result.stdout
    assert "provider: acme" in result.stdout
    assert BILLING.read_text(encoding="utf-8") == before


LAUNCH = ROOT / "docs" / "launch"


# Spec AC1/AC2/AC3: the kit covers the audience, the copy, the name risk and the checklist.
def test_the_launch_kit_is_complete():
    for name in (
        "LAUNCH.md",
        "FAQ.md",
        "GALLERY.md",
        "NAME_CHECK.md",
        "FIRST_COMMENT.md",
        "DEMO.md",
    ):
        assert (LAUNCH / name).read_text(encoding="utf-8").strip()

    launch = (LAUNCH / "LAUNCH.md").read_text(encoding="utf-8")
    for value in (
        "Blocker",
        "Tagline options",
        "What not to claim",
        "Launch-day checklist",
        "pip install",
        "self-hosted",
        "pre-1.0",
    ):
        assert value in launch

    faq = (LAUNCH / "FAQ.md").read_text(encoding="utf-8")
    for value in (
        "Is Tenon a SaaS?",
        "Does it push to my repository?",
        "Does it use an LLM?",
        "Does it auto-merge?",
        "What does it cost?",
        "How do I self-host it?",
    ):
        assert value in faq

    gallery = (LAUNCH / "GALLERY.md").read_text(encoding="utf-8")
    for value in ("## 1.", "## 2.", "## 3.", "## 4."):
        assert value in gallery

    name_check = (LAUNCH / "NAME_CHECK.md").read_text(encoding="utf-8")
    for value in ("tenonhq.com", "Blocker", "PyPI", "Product Hunt"):
        assert value in name_check

    comment = (LAUNCH / "FIRST_COMMENT.md").read_text(encoding="utf-8")
    assert "Product Hunt" in comment
