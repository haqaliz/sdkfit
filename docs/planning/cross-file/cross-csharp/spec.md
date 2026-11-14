# Spec: `cross-csharp` (T12e)

- **Feature:** `cross-file`
- **PRD:** `docs/planning/cross-file/prd.md` (§ M2, M6)
- **Boundary:** the C# directory/namespace method index, cross-file resolution and closure inheritance.

## In-scope requirements

- `scan_csharp(...)`: build an index from all `.cs` files in the same directory: each method name ->
  its return type chain, resolved in that file's namespace/using context. A `Helpers.MakeClient()` or
  a bare same-package call roots the assigned receiver.
- A duplicate method name in the package is ambiguous: no evidence.
- A local function/lambda inherits the enclosing receiver/parameter bindings; a local assignment
  rebinds/clears.
- No config change; the chain stays `Type.member...`; no new shapes/reasons/dynamics.

## Out-of-scope

- Cross-namespace/project references, repo-wide indexes, generics/overloads.

## Acceptance criteria

- **AC1 — Cross-file.** A method in `Helpers.cs` called from `Billing.cs` roots the receiver.
- **AC2 — Ambiguity.** Two methods with the same name in the directory are not evidence.
- **AC3 — Closure.** A local function/lambda uses the enclosing typed parameter/receiver; a local
  assignment rebinds/clears.
- **AC4 — Policy/regression.** A `locate_csharp` case; the existing C# tests green.
