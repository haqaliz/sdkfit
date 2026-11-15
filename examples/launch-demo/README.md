# Launch demo: Acme Payments 2.0

Acme shipped Payments 2.0 and renamed `amount` to `amount_cents`. The consumer package in `repo/`
still calls the old keyword; its tests only import the module, so nothing fails until production.

From the repository root:

```sh
bash scripts/launch_demo.sh
```

The script copies `repo/` to a temp directory and runs the shipped pipeline:

1. `tenon check` finds the affected call site and exits 1.
2. `tenon fix` rewrites `amount=` to `amount_cents=`, runs the proof command and exits 0.
3. `tenon provider migrate` runs the same migration from `bundle.json` (dry run: no PR).

Nothing in this directory is modified; the recorded transcript is `docs/launch/DEMO.md`.
