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
