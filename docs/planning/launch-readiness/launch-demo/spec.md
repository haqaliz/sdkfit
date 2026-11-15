# Spec: `launch-demo` (T16)

- **Feature:** `launch-readiness`
- **PRD:** `docs/planning/launch-readiness/prd.md` (§ M3, M5)
- **Boundary:** `examples/launch-demo/`, `scripts/launch_demo.sh`, `docs/launch/DEMO.md` and the
  demo test.

## In-scope requirements

- `examples/launch-demo/repo/`: a self-contained `acme` consumer package (client + billing) that
  calls `client.charges.create(amount=...)`; `old.yaml`/`new.yaml` rename `amount` to
  `amount_cents`; `bundle.json` (dry run, no PR); a README telling the story.
- `scripts/launch_demo.sh`: copies the demo repo to a temp dir, runs `tenon check` (expects exit 1
  and `1 certain site`), then `tenon fix` (expects exit 0 and `Proof: TESTS_PASSED`), and prints
  readable section headers; no network, no writes into the checkout.
- `docs/launch/DEMO.md`: the recorded transcript from a real run.
- `tests/test_launch.py`: runs the script (subprocess, timeout) and asserts the two outputs, and
  that the checked-in demo source is unchanged (`amount=amount` still present).
- `examples/README.md`: a pointer to the launch demo.

## Out-of-scope

- An asciinema/GIF, a hosted demo, network or PR calls, editing the test fixture.

## Acceptance criteria

- **AC1 — Check.** The demo locates exactly one certain site and exits 1.
- **AC2 — Fix.** The demo proposes `amount=amount` → `amount_cents=amount`, proves it and exits 0.
- **AC3 — Clean.** The checkout's demo source is unchanged; only the temp copy is modified.
- **AC4 — Transcript/test.** `DEMO.md` matches a real run; the test passes offline.
