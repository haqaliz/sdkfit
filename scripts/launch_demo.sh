#!/usr/bin/env bash
# The offline launch demo: locate, rewrite and prove one vendor rename.
set -euo pipefail

cd "$(dirname "$0")/.."

demo="examples/launch-demo"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cp -R "$demo/repo" "$tmp/repo"
old="$PWD/$demo/old.yaml"
new="$PWD/$demo/new.yaml"

echo "Acme Payments 2.0 renamed 'amount' to 'amount_cents'."
echo
echo "1) Find every affected call site"
set +e
uv run -q sdkfit check "$tmp/repo" \
  --old "$old" --new "$new" \
  --language python --sdk-package acme.client
status=$?
set -e
if [ "$status" -ne 1 ]; then
  echo "expected sdkfit check to exit 1, got $status" >&2
  exit 1
fi

echo
echo "2) Rewrite the call site and prove the change"
uv run -q sdkfit fix "$tmp/repo" \
  --old "$old" --new "$new" \
  --language python --sdk-package acme.client \
  --check "python3 -c 'import acme.billing'"

echo
echo "3) The same migration as a provider bundle (no PR)"
uv run -q sdkfit provider migrate "$tmp/repo" --bundle "$PWD/$demo/bundle.json"
