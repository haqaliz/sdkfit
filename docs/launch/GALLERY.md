# Gallery plan

The Product Hunt page needs a thumbnail and 3–4 gallery images. Capture real screens; do not invent
UI, votes or customer logos. Recommended size: **1270×760** (gallery), **240×240** (thumbnail).

## 1. Thumbnail

- **Caption:** Tenon — breaking API changes, fixed and proven.
- **Screen:** a dark terminal crop showing the `tenon fix` diff and `Proof: TESTS_PASSED`, with the
  product name set in the corner. No stock art.
- **Why:** the proof line is the differentiator; it must be readable at 240 px.

## 2. `tenon check` — the affected site

- **Caption:** Find the call sites a breaking change breaks.
- **Screen:** the exact block from [`DEMO.md`](DEMO.md):

  ```
  renamed #/components/schemas/Charge/properties: amount -> amount_cents
  acme/billing.py:7:34  keyword  amount

  1 change, 1 certain site, 0 ambiguity groups
  ```

- **Capture:** a 120×30 terminal, dark theme, font large enough to read at half width; crop to the
  command and these lines; no secrets or local paths.

## 3. `tenon fix` — the proof

- **Caption:** Rewrite only what it can prove.
- **Screen:** the `tenon fix` block: the one-line diff (`amount=` → `amount_cents=`) plus
  `Proof: TESTS_PASSED`, `Baseline exit: 0`, `After exit: 0`.
- **Why:** shows the change is small, reviewed and checked by the user's own command.

## 4. The flow

- **Caption:** From API diff to reviewed PR — without an LLM.
- **Screen:** a simple five-step diagram on the repo's dark/yellow palette:
  `detect → locate → propose → prove → PR`, with the proof labels
  (`TESTS_PASSED`, `CHARACTERIZED`, `REPLAYED`, `TYPES_BUILD_ONLY`) under `prove`.
- **Why:** explains the product in one image for people who will not read the README.

## Capture rules

- Use only the shipped outputs and the launch demo; no mocked screens.
- No customer names, tokens, private paths or unrelated browser tabs.
- Keep the product name consistent with the final name decision in
  [`NAME_CHECK.md`](NAME_CHECK.md); regenerate the images if the name changes.
- Check the small size: the caption and the proof line must remain legible as thumbnails.
