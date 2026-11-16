# Gallery plan

The Product Hunt page needs a thumbnail and 3–4 gallery images. The generated set is committed under
`assets/` (each PNG has an editable SVG source) and uses the official SDK Fit logo; use only real product
output, never mocked UI, votes or customer logos. Recommended size: **1270×760** (gallery), **1024×1024** (thumbnail), which is what
the committed assets use.

## 1. Thumbnail

- **Caption:** SDK Fit — breaking API changes, fixed and proven.
- **Asset:** `assets/thumbnail.png` (1024×1024; source `assets/thumbnail.svg`).
- **Screen:** the official SDK Fit logo alone on a dark square; no text, so the Product Hunt
  thumbnail and its social card stay brand-only.
- **Why:** the launch title and tagline carry the words; the mark is the thumbnail.

## 2. `sdkfit check` — the affected site

- **Caption:** Find the call sites a breaking change breaks.
- **Asset:** `assets/check.png` (1270×760; source `assets/check.svg`).
- **Screen:** the exact block from [`DEMO.md`](DEMO.md):

  ```
  renamed #/components/schemas/Charge/properties: amount -> amount_cents
  acme/billing.py:7:34  keyword  amount

  1 change, 1 certain site, 0 ambiguity groups
  ```

- **Note:** the image wraps the long rename line after the colon for legibility; the text is exact.

## 3. `sdkfit fix` — the proof

- **Caption:** Rewrite only what it can prove.
- **Asset:** `assets/fix.png` (1270×760; source `assets/fix.svg`).
- **Screen:** the one-line diff (`amount=` → `amount_cents=`), `Proof: TESTS_PASSED` and the proof
  command. The transcript's baseline/after exit lines are omitted to keep the image readable.
- **Why:** shows the change is small, reviewed and checked by the user's own command.

## 4. The flow

- **Caption:** From API diff to reviewed PR — without an LLM.
- **Asset:** `assets/flow.png` (1270×760; source `assets/flow.svg`).
- **Screen:** a five-step diagram on the repo's dark/yellow palette:
  `detect → locate → propose → prove → PR`, with the proof labels
  (`TESTS_PASSED`, `CHARACTERIZED`, `REPLAYED`, `TYPES_BUILD_ONLY`) in the panel below.
- **Why:** explains the product in one image for people who will not read the README.

## Capture rules

- Use only the shipped outputs and the launch demo; no mocked screens or customer logos.
- No customer names, tokens, private paths or unrelated browser tabs.
- The PNGs are rendered from the committed SVGs with
  `rsvg-convert -w 1270 -h 760 assets/check.svg -o assets/check.png` (thumbnail:
  `-w 1024 -h 1024`); edit the SVG, not the PNG.
- Keep the product name consistent with [`NAME_CHECK.md`](NAME_CHECK.md); regenerate the images if it
  changes.
- Check the small size: the caption and the proof line must remain legible as thumbnails.
