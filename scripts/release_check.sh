#!/usr/bin/env bash
# Local release check: tests, build, and a clean-venv install of the wheel.
set -euo pipefail

cd "$(dirname "$0")/.."
VERSION="0.4.0"

uv sync --frozen
uv run pytest
uv run sdkfit --version | grep -qx "sdkfit ${VERSION}"

rm -rf dist
uv build

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
uv venv "$tmp/venv"
uv pip install --python "$tmp/venv/bin/python" --quiet dist/sdkfit-*.whl
"$tmp/venv/bin/sdkfit" --version | grep -qx "sdkfit ${VERSION}"
"$tmp/venv/bin/sdkfit" check --help >/dev/null

echo "release check ok: sdkfit ${VERSION}"
