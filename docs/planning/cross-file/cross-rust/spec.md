# Spec: `cross-rust` (T12e)

- **Feature:** `cross-file`
- **PRD:** `docs/planning/cross-file/prd.md` (§ M5, M6)
- **Boundary:** the Rust module index, `mod`/`use` resolution and closure inheritance.

## In-scope requirements

- `scan_rust(...)`: resolve `mod helpers;` to `helpers.rs`/`helpers/mod.rs` (relative to the file's
  directory or the crate `src/`), index the module's function return types (resolved in the defining
  file's crate roots/aliases), and root the assigned receiver from:
  - `use crate::helpers::make_client;` + `make_client()`,
  - `use helpers::make_client;` (when `mod helpers;` is in scope) + `make_client()`,
  - `crate::helpers::make_client()` / `helpers::make_client()`.
- A function name defined twice in one module is ambiguous: no evidence; the same name in different
  modules is fine (module-qualified).
- A `closure_expression` inherits the enclosing receiver/parameter bindings; a nested `fn` resets
  (Rust nested functions do not capture). A local assignment rebinds/clears.
- No config change; the chain stays `Type.member...`; no new shapes/reasons/dynamics.

## Out-of-scope

- External crate modules, re-exports/`pub use`, generics, trait methods, `include!`.

## Acceptance criteria

- **AC1 — Module file.** A helper in `helpers.rs` (or `helpers/mod.rs`) called via `use`/a path roots
  the receiver.
- **AC2 — Ambiguity.** Two definitions in one module are not evidence; same names in different
  modules resolve by path.
- **AC3 — Closure.** A closure captures the enclosing typed parameter/receiver; a nested `fn` does
  not; a local assignment rebinds/clears.
- **AC4 — Policy/regression.** A `locate_rust` case; the existing Rust tests green.
