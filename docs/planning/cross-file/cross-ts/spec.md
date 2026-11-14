# Spec: `cross-ts` (T12e)

- **Feature:** `cross-file`
- **PRD:** `docs/planning/cross-file/prd.md` (§ M4, M6)
- **Boundary:** the TypeScript relative-import module index and nested-function inheritance.

## In-scope requirements

- `scan_ts(...)`: resolve relative imports (`./helpers`, `../lib/helpers`) to a same-package file
  (try `.ts/.tsx/.mts/.cts/.js/.jsx/.mjs/.cjs` and `/index.*`), index the function/method return
  types per module (resolved in the defining file's imports), and root the assigned receiver from a
  call to an imported function or a namespace member.
- A function name defined twice in one module is ambiguous: no evidence; the same name in different
  modules is fine (import-qualified).
- A nested function/arrow inherits the enclosing receiver/parameter bindings; a top-level function
  resets. A local assignment rebinds/clears.
- No config change; the chain stays `Type.member...`; no new shapes/reasons/dynamics.

## Out-of-scope

- Package/`node_modules` resolution, `*` imports, dynamic imports, declaration files.

## Acceptance criteria

- **AC1 — Relative import.** A helper in `./helpers` (named/default/namespace import) roots the
  receiver.
- **AC2 — Index.** A `./helpers/index.ts` resolves; an unresolved relative path is not evidence.
- **AC3 — Ambiguity.** Two definitions in one module are not evidence; same names in different
  modules resolve per import.
- **AC4 — Closure.** A nested function/arrow uses the enclosing typed parameter/receiver; a local
  assignment rebinds/clears.
- **AC5 — Policy/regression.** A `locate_ts` case; the existing TS/JS tests green.
