# Spec: `postgres-cli` (T15)

- **Feature:** `cloud-deploy`
- **PRD:** `docs/planning/cloud-deploy/prd.md` (§ M2, M6)
- **Boundary:** the `provider serve` store selection, the stale recovery lease and the CLI tests.
  No store internals, manifests or docs.

## In-scope requirements

- `provider serve --database-url URL` (or `TENON_DATABASE_URL`). Exactly one of `--db`/
  `--database-url` (or its env) is required; zero or both is a named usage error (exit 2).
- A small `_open_store(db, database_url)` factory: Postgres when a URL is given, SQLite otherwise.
  A missing `psycopg` (the store raises `StoreError`) becomes a named usage error.
- Startup recovery passes a stale-lease cutoff (`now - --run-timeout`) so a replica never re-queues a
  live peer's run; SQLite ignores the cutoff (single process).
- `--help` lists `--database-url`; the worker/API wiring is unchanged.
- Tests: URL/env selection, both/none usage errors, the recover cutoff, the missing-driver usage
  error, the help flag; the existing serve tests green.

## Out-of-scope

- The Postgres store itself; SQLite behavior; the Kubernetes manifests/docs.

## Acceptance criteria

- **AC1 — Selection.** `--database-url`/`TENON_DATABASE_URL` constructs the Postgres store with that
  DSN; `--db` constructs the SQLite store.
- **AC2 — Exactly one.** Both or neither is exit 2 with a named message; no store is opened.
- **AC3 — Recovery.** The Postgres path calls `recover(older_than=now - run_timeout)`; SQLite still
  recovers stranded rows.
- **AC4 — Missing driver.** A missing `psycopg` is exit 2 naming the `postgres` extra, not a
  traceback.
- **AC5 — Regression.** Existing CLI/service tests green.
