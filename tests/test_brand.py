"""The shipped surfaces carry only the SDK Fit name."""

from pathlib import Path

ROOT = Path(__file__).parent.parent
ROOTS = ("src", "deploy", "scripts", "examples", ".github", "bundles", "secrets")
FILES = (
    "pyproject.toml",
    "Dockerfile",
    "docker-compose.yml",
    "Caddyfile",
    "README.md",
    "VISION.md",
    "CLAUDE.md",
    ".env.example",
    "LICENSE",
    "uv.lock",
)
EXEMPT = {
    ROOT / "docs" / "launch" / "NAME_CHECK.md",
    ROOT / "CHANGELOG.md",
}
BINARY = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".whl", ".gz", ".pyc"}


def a_surfaces():
    paths = [ROOT / name for name in FILES]
    for name in ROOTS:
        base = ROOT / name
        if base.exists():
            paths.extend(base.rglob("*"))
    paths.extend((ROOT / "docs").rglob("*.md"))
    return paths


# Spec AC3: no shipped file may carry the previous name, its env prefix or its module path.
def test_no_old_name_in_shipped_surfaces():
    offenders = []
    for path in a_surfaces():
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or path.suffix in BINARY:
            continue
        if "planning" in path.parts or path in EXEMPT:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if "tenon" in text.lower():
            offenders.append(str(path.relative_to(ROOT)))

    assert offenders == []
