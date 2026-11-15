# Spec: `postgres-store` (T15)

- **Feature:** `cloud-deploy`
- **PRD:** `docs/planning/cloud-deploy/prd.md` (§ M1, M6)
- **Boundary:** the `Store` protocol, `PostgresRunStore`, the optional dependency and the fake-driver tests.

## In-scope requirements

- `src/tenon/service/store.py`: a `Store` protocol covering `create_run`, `claim_next`, `requeue`,
  `finish`, `get`, `list`, `find_by_idempotency_key`, `record_event`, `request_cancel`,
  `cancel_requested`, `counts`, `recover(older_than=None)`, `ping`, `close`. `RunStore` satisfies it
  (no behavior change).
- `src/tenon/service/postgres.py`: `PostgresRunStore(dsn, *, connect=None)`:
  - lazy `psycopg` import; a missing driver is a named `StoreError`;
  - schema `runs` (`id text pk, bundle, status, created_at timestamptz, started_at, finished_at,
    exit int, report jsonb, error, idempotency_key text unique, attempts int, cancel_requested bool`)
    and `events` (`id bigserial pk, delivery text unique, event, action, installation, received_at,
    payload jsonb`), created on open;
  - `claim_next`: one transaction, `SELECT id FROM runs WHERE status='queued' ORDER BY created_at, id
    FOR UPDATE SKIP LOCKED LIMIT 1`, then `UPDATE ... status='running', started_at=now(),
    attempts=attempts+1 RETURNING ...`;
  - `create_run` uses `ON CONFLICT (idempotency_key) DO NOTHING` + select; `requeue`; `finish`
    (`succeeded|failed|cancelled`); `request_cancel`/`cancel_requested`; `counts` (five statuses);
    `recover(older_than)`: only `running` rows with `started_at < older_than` (or cancel_requested),
    never a live peer's; `ping` = `SELECT 1 FROM runs LIMIT 1`; `close`.
  - Return the same `Run`/`Event` values as SQLite.
- `pyproject.toml`: a `postgres` optional extra (`psycopg[binary]>=3.2`); the core install unchanged.
- Tests: a fake executor/connection that records SQL and returns scripted rows; create/claim
  (asserts `FOR UPDATE SKIP LOCKED`)/idempotency/requeue/finish/cancel/counts/recover/ping; the
  missing-driver error; no live DB. The existing `RunStore` tests green.

## Out-of-scope

- The CLI factory/flag; the Kubernetes manifests; docs.
- Redis, migrations beyond `CREATE TABLE IF NOT EXISTS`, HA.

## Acceptance criteria

- **AC1 — Protocol.** `RunStore` satisfies `Store`; the Postgres class implements every method.
- **AC2 — Claim.** The SQL includes `FOR UPDATE SKIP LOCKED` and the transaction sets
  running/started_at/attempts for the selected row; two claims get different rows (scripted).
- **AC3 — Semantics.** Create/idempotency/requeue/finish/cancel/counts/events/ping/recover match the
  SQLite rules; recovery only touches rows older than the cutoff.
- **AC4 — Driver.** A missing `psycopg` is a named `StoreError`; an injected fake needs no dependency.
- **AC5 — Regression.** All prior service tests green.
