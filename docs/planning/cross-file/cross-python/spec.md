# Spec: `cross-python` (T12e)

- **Feature:** `cross-file`
- **PRD:** `docs/planning/cross-file/prd.md` (§ M3, M6)
- **Boundary:** the Python module index, import resolution and nested-function inheritance.

## In-scope requirements

- `scan(...)`: build a module index from the repo's `.py` files (`pkg/helpers.py` -> `pkg.helpers`,
  `pkg/__init__.py` -> `pkg`, top-level `helpers.py` -> `helpers`), with each function's return chain
  resolved in its file's imports/roots. Resolve:
  - `from .helpers import make_client` (relative to the caller's package),
  - `from pkg.helpers import make_client` (absolute),
  - `import pkg.helpers` + `pkg.helpers.make_client()`,
  - `from . import helpers` + `helpers.make_client()`.
  A call to an indexed function/module attribute roots the assigned receiver.
- A function name defined twice in the same module is ambiguous: no evidence. The same name in
  different modules is fine (module-qualified).
- A nested `def`/lambda inherits the enclosing receiver/parameter bindings; a local assignment
  rebinds/clears.
- No config change; the chain stays `Type.member...`; no new shapes/reasons/dynamics.

## Out-of-scope

- Installed-package discovery, `*` imports, dynamic imports, repo-wide name indexes.

## Acceptance criteria

- **AC1 — Relative/absolute imports.** A helper in `pkg/helpers.py` imported either way roots the
  receiver.
- **AC2 — Module attribute.** `import pkg.helpers; pkg.helpers.make_client()` roots.
- **AC3 — Ambiguity.** Two definitions in one module are not evidence; same names in different
  modules resolve per import.
- **AC4 — Closure.** A nested `def`/lambda uses the enclosing typed parameter/receiver; a local
  assignment rebinds/clears.
- **AC5 — Policy/regression.** A `locate` case; the existing Python tests green.
