# Card: feat/cross-file

- **Source:** FALLBACK — no GitHub issue (`gh issue list` is empty).
- **Owner:** aliz
- **Type:** feat
- **Capability:** **T12 Receiver tracking** — deeper slice: **cross-file inference** (T12e)
- **Milestone:** after T12d; the receiver follow-up
- **State:** T12e shipped 2026-11-15 (`src/tenon/locate/*_scan.py`, cross-file signatures and closures; 2,719 tests)
- **Branch:** `feat/cross-file/aliz`
- **Worktree:** `.claude/worktrees/feat-cross-file`

## Brief

T12c/T12d infer a receiver from an annotated return type or parameter **in the same file**. A helper
is often defined in another file of the same package/module/namespace:

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
client.Charges.Create(...);
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

T12e extends the annotated-signature inference across files within the same package/module/namespace
(or, if chosen, the repository), and optionally captures an outer typed parameter inside a nested
function. Only written annotations count; a duplicate name across files is not evidence (ambiguous),
not a guess.

## Constraints carried in from the repo

- T12a–T12d's receiver bindings and signature maps are the base; extend, do not fork.
- The crate/package/namespace/import roots and aliases resolve the types; the new part is the
  file/package index and import/module resolution.
- Stdlib/tree-sitter/`ast` only; offline fixtures/tests.
- The shared `derive`/`resolve` policy decides certainty.

## Scope fence

Not this card: unannotated inference, SDK return types without an annotation/mapping, full type
inference, generics/overload resolution, a service change.
