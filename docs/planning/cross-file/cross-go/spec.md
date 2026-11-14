# Spec: `cross-go` (T12e)

- **Feature:** `cross-file`
- **PRD:** `docs/planning/cross-file/prd.md` (§ M1, M6)
- **Boundary:** the Go package index, same-package call resolution and closure inheritance.

## In-scope requirements

- `scan_go(...)`: build a package index from all `.go` files in the same directory: each `func` name
  -> its result type chain, resolved in that file's import context (single result or the first of a
  result list). A bare call to an indexed same-package function roots the assigned receiver.
- A duplicate function name in the package (multiple definitions) is ambiguous: no evidence.
- A `func_literal` (closure) inherits the enclosing receiver/parameter bindings; a local assignment
  rebinds/clears.
- No config change; `receivers` still applies. The chain stays `Type.member...`; no new shapes/
  reasons/dynamics.

## Out-of-scope

- Cross-package imports, repo-wide indexes, generics, unannotated results.

## Acceptance criteria

- **AC1 — Cross-file.** A helper in `helpers.go` called from `billing.go` roots the receiver.
- **AC2 — Ambiguity.** Two definitions of the same name in the package (same or different results)
  are not evidence.
- **AC3 — Closure.** A `func_literal` uses the enclosing typed parameter/receiver; a local
  assignment rebinds/clears.
- **AC4 — Policy/regression.** A `locate_go` case; the existing Go tests green.
