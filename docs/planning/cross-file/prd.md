# PRD: Cross-file receiver inference (T12e)

- **Slug:** `cross-file`
- **Capability:** **T12 Receiver tracking** — deeper slice: **cross-file signatures and closures**
- **Milestone:** after T12d; the receiver follow-up
- **Status:** implemented 2026-11-15 (`src/tenon/locate/*_scan.py`, cross-file signatures and closures; 2,719 tests)
- **Card:** `docs/planning/_card/issue.md`

## Problem Statement

T12c/T12d infer a receiver from an annotated return type or parameter **in the same file**. Helpers
are usually defined in another file of the same package/module/namespace:

```go
// helpers.go
func newClient() *stripe.Client { ... }
// billing.go
client := newClient()
client.Charges.New(...)
```
```csharp
// Helpers.cs
static StripeClient MakeClient() => ...;
// Billing.cs
var client = Helpers.MakeClient();
```
```python
# helpers.py
def make_client() -> stripe.Client: ...
# billing.py
from .helpers import make_client
client = make_client()
```
```ts
// helpers.ts
export function makeClient(): StripeClient { ... }
// billing.ts
import { makeClient } from "./helpers";
const client = makeClient();
```
```rust
// helpers.rs
pub fn make_client() -> Client { ... }
// billing.rs
use crate::helpers::make_client;
let client = make_client();
```

Closures add a second gap: a nested function/lambda that captures an outer typed parameter (or a
rooted receiver) loses the binding when the scanner resets the scope.

T12e adds **cross-file signatures and closure capture** in all five languages:
- build a package/module/namespace index of annotated function/method return types, resolved in the
  defining file's import context;
- resolve a same-package/relative-module call to the indexed signature and root the assigned
  receiver;
- inherit the enclosing receiver/parameter bindings into a nested function/closure (a local
  assignment still rebinds/clears);
- a duplicate annotated name across files is ambiguous, never evidence.

Only written annotations count. No unannotated inference, no repo-wide name lookup, no generics.

**For whom:** a provider migrating a repo whose helpers span files, a self-hoster, and the reviewer
of the located sites.

## Goals & Success Metrics

1. **One index per package.** Each scanner builds an index of annotated return types across the
   files of the package/module/namespace, resolving each type in its defining file's context.
2. **One resolution rule.** A same-package/relative-module call roots the assigned receiver; a
   cross-package/cross-file-outside-the-package call is not evidence.
3. **Closures.** A nested function/lambda/closure inherits the enclosing receiver/parameter
   bindings; a local assignment rebinds/clears.
4. **Ambiguity is honest.** A duplicate annotated name or a conflicting return type across files is
   not evidence.
5. **The same chain/policy.** `Type.member...`; the shared `derive`/`resolve` decides; no new
   vocabulary.
6. **Offline tests.** Per language: a helper in another file, a relative import/module, a duplicate
   name, an unannotated helper, a closure capture, a rebinding, the existing suites green.

## Requirements

### Must have

- **M1 — Go.** Index `func` result types across the `.go` files in the same directory/package,
  resolving each in its file's import context; a bare same-package call roots; a duplicate name is
  not evidence; a `func_literal` inherits the enclosing bindings.
- **M2 — C#.** Index method/local-function return types across the `.cs` files in the same
  directory/namespace, resolving each in its file's using context; a `Helpers.MakeClient()` or a
  bare same-namespace call roots; a duplicate name is not evidence; a local function/lambda inherits.
- **M3 — Python.** Index module function return types (`acme/helpers.py` -> `acme.helpers`),
  resolving each in its file's imports; `from .helpers import make_client`,
  `from acme.helpers import make_client`, `import acme.helpers` + `acme.helpers.make_client()`
  root; a duplicate name is not evidence; a nested `def`/lambda inherits.
- **M4 — TypeScript.** Resolve relative imports (`./helpers`, `../lib/helpers`, `index.*`) to a
  same-package file; index exported function return types; a duplicate name is not evidence; a nested
  function/arrow inherits.
- **M5 — Rust.** Resolve `mod helpers;` + `use crate::helpers::make_client` /
  `crate::helpers::make_client()` / `helpers::make_client()` to `helpers.rs`/`helpers/mod.rs`; index
  the function return types; a duplicate name is not evidence; a `closure_expression` inherits (a
  nested `fn` does not capture).
- **M6 — Policy.** Each language reuses its roots/aliases and the shared `resolve`; the chain stays
  `Type.member...`; no new shapes/reasons/dynamics.
- **M7 — Tests/docs.** Per-language cross-file/duplicate/closure/rebinding tests, a policy case and
  an end-to-end `tenon check` cross-file fixture; README/ARCHITECTURE/CHANGELOG `Unreleased`/
  capability roadmap T12e. Offline.

### Should have

- **S1 — Two passes.** Build the package index (resolved signatures) before the file's call/receiver
  pass; no quadratic re-parsing.
- **S2 — Deterministic.** Files sorted; duplicate/ambiguity detection stable.
- **S3 — No config change.** `receivers` remains the escape hatch.

### Nice to have

- **N1 — Repo-wide indexes**; a later slice.
- **N2 — SDK return types without an annotation/mapping**; not evidence.
- **N3 — Generics/overloads**; out of scope.

## Data Model

No new config/hit type. A package-level `name -> type chain | ambiguous` index feeds the existing
receiver binding; the hit chain is `Type.member...`.

## API Contract

No CLI/config change. The inferred evidence is automatic; `--receiver` still overrides/extends.

## Technical Considerations

- **Why a package index.** A cross-file helper's return type must be resolved in its own file's
  import context; the caller's context may not even import the SDK type.
- **Why same-package.** A repo-wide name index collides; the package/module/namespace is the certain
  unit.
- **Why ambiguous duplicates.** Two same-name helpers can return different SDK types; picking one is
  a guess. The report stays silent.
- **Why inherit closures.** A closure sees the enclosing typed parameter; resetting loses real
  evidence. A local assignment still wins.

## Risks & Open Questions

- **Module resolution complexity.** Rust module trees, Python package `__init__`, TS `index.*` and Go
  directory packages differ; each aspect implements its language's rule and tests it.
- **Duplicates.** Any duplicate annotated name in the package is not evidence (conservative).
- **Closure shadowing.** A local assignment/parameter in the nested scope rebinds; an outer parameter
  captured by reference keeps the type unless rebound.
- **Cross-package helpers.** A helper imported from another package is not followed; the provider can
  annotate the assignment or map a factory.
- **Open question — should a same-name duplicate with the same return type root?** No in this slice;
  any duplicate is ambiguous. A later refinement can compare the chains.

## Out of Scope

- Repo-wide name lookup, SDK return types without an annotation/mapping, generics/overloads.
- New proof levels/ambiguity reasons; a service/deployment change.

## Aspect Proposals (for `tech-plan`)

| Aspect | Boundary |
|---|---|
| `cross-go` | The Go package index, same-package call resolution and closure inheritance. |
| `cross-csharp` | The C# directory/namespace index, cross-file method resolution and closure inheritance. |
| `cross-python` | The Python module index, relative/absolute import resolution and nested-function inheritance. |
| `cross-ts` | The TS relative-import index and nested-function inheritance. |
| `cross-rust` | The Rust module index, `mod`/`use` resolution and closure inheritance. |
| `cross-docs` | README/ARCHITECTURE/CHANGELOG/roadmap, the end-to-end fixture, the full suite. |

## Self-critique (prd-generator pass)

| Dimension | Rating | Note |
|---|---|---|
| Problem definition | 🟢 | Helpers span files; closures lose bindings. |
| User understanding | 🟢 | Provider/self-hoster/reviewer; the per-language example is concrete. |
| Success metrics | 🟢 | One index/rule, closures, ambiguity, same policy, offline tests. |
| Scope clarity | 🟢 | Same-package only; duplicates/ambiguity explicit; no repo-wide. |
| Edge cases & risks | 🟡 | Module resolution and duplicate names are the real complexity; documented/tested. |
| Stakeholder alignment | 🟡 | Solo project; the review gate is the approver. |
| Feasibility | 🟢 | Extends the existing scanners/roots; no dependency. |
| Go-to-market | 🟢 | Removes the biggest remaining receiver gap. |

**Areas to strengthen before sharing:** cross-file module resolution is the most complex locator work
so far; each language's rule is scoped to the same package and covered by tests. Duplicates stay
ambiguous.

**The question I would want answered before greenlighting this:** *If two files define `make_client`
with different SDK return types, which one roots?* The answer this card records: neither; the name is
ambiguous and the assignment stays unrooted. The report does not guess.
