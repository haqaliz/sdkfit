"""The Postgres store against a scripted fake driver; no live database."""

import builtins
import json
from datetime import datetime, timezone

import pytest

from tenon.service import RunStore
from tenon.service import postgres as postgres_module
from tenon.service.postgres import PostgresRunStore
from tenon.service.store import Store, StoreError

NOW = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)
STAMP = "2026-11-16T12:00:00+00:00"
COLUMNS = (
    "id, bundle, status, created_at, started_at, finished_at, exit, report,"
    " error, idempotency_key, attempts, cancel_requested"
)


class FakeCursor:
    def __init__(self, rows=()):
        self._rows = list(rows)

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)


class FakeConnection:
    """Records SQL and returns the next scripted rows; schema calls are free."""

    def __init__(self, *responses):
        self.calls = []
        self._responses = list(responses)
        self.closed = False

    def execute(self, sql, params=None):
        flat = " ".join(sql.split())
        self.calls.append((flat, params))
        if flat.startswith("CREATE"):
            return FakeCursor()
        rows = self._responses.pop(0) if self._responses else ()
        return FakeCursor(rows)

    def close(self):
        self.closed = True


class BrokenConnection(FakeConnection):
    def execute(self, sql, params=None):
        if " ".join(sql.split()).startswith("CREATE"):
            return super().execute(sql, params)
        raise RuntimeError("connection lost")


def a_row(
    id="run-1",
    bundle="bundle.json",
    status="queued",
    created_at=NOW,
    started_at=None,
    finished_at=None,
    exit=None,
    report=None,
    error=None,
    idempotency_key=None,
    attempts=0,
    cancel_requested=False,
):
    return (
        id,
        bundle,
        status,
        created_at,
        started_at,
        finished_at,
        exit,
        report,
        error,
        idempotency_key,
        attempts,
        cancel_requested,
    )


def a_store(*responses, connection=None):
    connection = connection or FakeConnection(*responses)

    def connect(_dsn):
        return connection

    return (
        PostgresRunStore(
            "postgresql://db/tenon",
            connect=connect,
            now=lambda: NOW,
            new_id=lambda: "run-1",
        ),
        connection,
    )


def a_run_calls(connection):
    """The non-schema statements and their parameters."""
    return [
        (sql, params)
        for sql, params in connection.calls
        if not sql.startswith("CREATE")
    ]


def a_run_sql(connection):
    """The non-schema statements, flattened for substring checks."""
    return [sql for sql, _params in a_run_calls(connection)]


# Spec AC4: an injected connection avoids the optional dependency entirely.
def test_an_injected_connection_needs_no_driver():
    seen = []
    connection = FakeConnection()

    PostgresRunStore(
        "postgresql://db/tenon",
        connect=lambda dsn: (seen.append(dsn), connection)[1],
    )

    assert seen == ["postgresql://db/tenon"]


# Spec AC4: a missing driver is a named StoreError, not a traceback.
def test_a_missing_driver_is_a_named_error(monkeypatch):
    real_import = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name == "psycopg":
            raise ImportError("no psycopg")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)

    with pytest.raises(StoreError, match="postgres"):
        PostgresRunStore("postgresql://db/tenon")


# Spec AC1/AC4: both backends satisfy the shared protocol.
def test_both_stores_satisfy_the_protocol():
    pg, _connection = a_store()

    assert isinstance(pg, Store)
    assert isinstance(RunStore(":memory:"), Store)


# Spec AC1: the schema is created on open with jsonb/timestamptz columns.
def test_the_schema_is_created_on_open():
    _store, connection = a_store()

    sql = " ".join(sql for sql, _params in connection.calls)
    assert "CREATE TABLE IF NOT EXISTS runs" in sql
    assert "CREATE TABLE IF NOT EXISTS events" in sql
    assert "TIMESTAMPTZ" in sql.upper()
    assert "JSONB" in sql.upper()
    assert "CREATE INDEX IF NOT EXISTS" in sql


# Spec AC2: a claim locks the oldest queued row and skips another pod's row.
def test_claim_next_uses_skip_locked_and_marks_running():
    claimed = a_row(
        status="running", started_at=NOW, attempts=1
    )
    store, connection = a_store((claimed,))

    run = store.claim_next()

    assert run is not None
    assert run.id == "run-1"
    assert run.status == "running"
    assert run.attempts == 1
    assert run.started_at == STAMP
    sql = a_run_sql(connection)[0]
    assert "FOR UPDATE SKIP LOCKED" in sql
    assert "UPDATE runs" in sql
    assert "status = 'running'" in sql
    assert "attempts = attempts + 1" in sql


def test_claim_next_on_an_empty_queue_is_none():
    store, _connection = a_store(())

    assert store.claim_next() is None


# Spec AC3: create uses the unique idempotency key as the dedupe seam.
def test_create_run_inserts_a_queued_row():
    store, connection = a_store(())

    run = store.create_run("bundle.json")

    assert run.status == "queued"
    assert run.bundle == "bundle.json"
    assert run.created_at == STAMP
    assert run.idempotency_key is None
    sql = a_run_sql(connection)[0]
    assert sql.startswith("INSERT INTO runs")
    assert "ON CONFLICT (idempotency_key) DO NOTHING" in sql


def test_create_run_returns_an_existing_key_without_inserting():
    existing = a_row(id="old", idempotency_key="hook:1")
    store, connection = a_store((existing,))

    run = store.create_run("bundle.json", idempotency_key="hook:1")

    assert run.id == "old"
    assert a_run_sql(connection) == [
        f"SELECT {COLUMNS} FROM runs WHERE idempotency_key = %s"
    ]


def test_create_run_reads_back_the_winner_of_a_conflict():
    winner = a_row(id="winner", idempotency_key="hook:1")
    store, connection = a_store((), (), (winner,))

    run = store.create_run("bundle.json", idempotency_key="hook:1")

    assert run.id == "winner"


# Spec AC3: requeue keeps the attempt count and clears the attempt data.
def test_requeue_puts_a_running_row_back_in_the_queue():
    running = a_row(status="running", started_at=NOW, attempts=2)
    queued = a_row(status="queued", attempts=2)
    store, connection = a_store((running,), (), (queued,))

    run = store.requeue("run-1")

    assert run.status == "queued"
    assert run.started_at is None
    assert run.attempts == 2
    statements = a_run_sql(connection)
    assert "status = 'queued'" in statements[1]
    assert "attempts" not in statements[1]


def test_requeue_an_unknown_run_is_a_named_error():
    store, _connection = a_store(())

    with pytest.raises(ValueError, match="unknown run"):
        store.requeue("missing")


def test_requeue_a_queued_run_is_a_named_error():
    store, connection = a_store((a_row(status="queued"),))

    with pytest.raises(ValueError, match="not running"):
        store.requeue("run-1")
    assert len(a_run_sql(connection)) == 1


# Spec AC3: finish stores the report as jsonb and records the exit code.
def test_finish_stores_the_terminal_status():
    running = a_row(status="running", started_at=NOW, attempts=1)
    finished = a_row(
        status="succeeded",
        started_at=NOW,
        finished_at=NOW,
        exit=0,
        report={"schema": {"amount": "amount_cents"}},
        attempts=1,
    )
    store, connection = a_store((running,), (), (finished,))

    run = store.finish(
        "run-1",
        status="succeeded",
        exit=0,
        report={"schema": {"amount": "amount_cents"}},
    )

    assert run.status == "succeeded"
    assert run.exit == 0
    assert run.report == {"schema": {"amount": "amount_cents"}}
    update_sql, params = connection.calls[-2]
    assert "report = %s::jsonb" in update_sql
    assert json.loads(params[3]) == {"schema": {"amount": "amount_cents"}}


def test_finish_rejects_an_invalid_status():
    store, connection = a_store()

    with pytest.raises(ValueError, match="invalid finish status"):
        store.finish("run-1", status="queued", exit=0, report=None)
    assert a_run_sql(connection) == []


def test_finish_an_unknown_run_is_a_named_error():
    store, _connection = a_store(())

    with pytest.raises(ValueError, match="unknown run"):
        store.finish("missing", status="failed", exit=1, report=None)


# Spec AC3: queued runs cancel now; running runs get the worker flag.
def test_cancelling_a_queued_run_finishes_it():
    queued = a_row(status="queued")
    cancelled = a_row(status="cancelled", finished_at=NOW)
    store, connection = a_store((queued,), (), (cancelled,))

    run = store.request_cancel("run-1")

    assert run.status == "cancelled"
    assert "status = 'cancelled'" in a_run_sql(connection)[1]


def test_cancelling_a_running_run_sets_the_flag():
    running = a_row(status="running", started_at=NOW)
    flagged = a_row(status="running", started_at=NOW, cancel_requested=True)
    store, connection = a_store((running,), (), (flagged,))

    run = store.request_cancel("run-1")

    assert run.status == "running"
    assert run.cancel_requested is True
    assert "cancel_requested = TRUE" in a_run_sql(connection)[1]


def test_cancelling_an_unknown_run_is_none():
    store, _connection = a_store(())

    assert store.request_cancel("missing") is None


def test_cancel_requested_reads_the_flag():
    store, _connection = a_store(((True,),))
    assert store.cancel_requested("run-1") is True

    store, _connection = a_store(())
    assert store.cancel_requested("missing") is False


# Spec AC3: recovery never steals a live row unless it is older than the lease.
def test_recover_uses_the_stale_cutoff():
    store, connection = a_store((("a",),), (("b",), ("c",)))

    recovered = store.recover(older_than=NOW)

    assert recovered == 3
    requeue_sql, requeue_params = a_run_calls(connection)[1]
    assert "NOT cancel_requested" in requeue_sql
    assert "started_at < %s" in requeue_sql
    assert requeue_params == (NOW,)


def test_recover_cancels_requested_rows_before_requeueing():
    store, connection = a_store((("a",),), ())

    assert store.recover(older_than=NOW) == 1
    cancel_sql = a_run_sql(connection)[0]
    assert "status = 'cancelled'" in cancel_sql
    assert "cancel_requested" in cancel_sql


def test_recover_without_a_cutoff_requeues_every_running_row():
    store, connection = a_store((), (("b",),))

    assert store.recover() == 1
    requeue_sql, requeue_params = a_run_calls(connection)[1]
    assert "started_at <" not in requeue_sql
    assert requeue_params is None


# Spec AC3: counts report every status, including the zeros.
def test_counts_reports_every_status():
    store, _connection = a_store((("queued", 2), ("failed", 1)))

    assert store.counts() == {
        "queued": 2,
        "running": 0,
        "succeeded": 0,
        "failed": 1,
        "cancelled": 0,
    }


def test_get_reads_one_run_or_none():
    store, _connection = a_store((a_row(),))

    assert store.get("run-1").id == "run-1"

    store, _connection = a_store(())
    assert store.get("missing") is None


def test_find_by_idempotency_key_reads_one_run():
    store, connection = a_store((a_row(id="k", idempotency_key="hook:1"),))

    run = store.find_by_idempotency_key("hook:1")

    assert run.id == "k"
    assert a_run_sql(connection) == [
        f"SELECT {COLUMNS} FROM runs WHERE idempotency_key = %s"
    ]


def test_list_clamps_the_limit():
    store, connection = a_store((a_row(),), (a_row(),))

    store.list(999)
    store.list(0)

    params = [params for _sql, params in connection.calls if params][-2:]
    assert params == [(200,), (1,)]


# Spec AC3: a duplicate delivery is recorded once.
def test_record_event_uses_the_unique_delivery():
    store, connection = a_store(((1,),))

    assert store.record_event(
        "d-1", "push", action="created", payload={"action": "created"}
    ) is True
    sql, params = a_run_calls(connection)[0]
    assert "INSERT INTO events" in sql
    assert "ON CONFLICT (delivery) DO NOTHING" in sql
    assert json.loads(params[4]) == {"action": "created"}


def test_a_duplicate_event_is_false():
    store, _connection = a_store()

    assert store.record_event("d-1", "push") is False


# Spec AC3: readiness reads the schema; any failure is not ready.
def test_ping_reads_the_schema():
    store, connection = a_store((("x",),))

    assert store.ping() is True
    assert a_run_sql(connection) == ["SELECT 1 FROM runs LIMIT 1"]


def test_ping_is_false_when_the_database_fails():
    store, _connection = a_store(connection=BrokenConnection(((),)))

    assert store.ping() is False


def test_close_closes_the_connection():
    store, connection = a_store()

    store.close()

    assert connection.closed is True


def test_a_connection_error_is_a_named_error():
    def connect(_dsn):
        raise OSError("no route to host")

    with pytest.raises(StoreError, match="connect"):
        PostgresRunStore("postgresql://db/tenon", connect=connect)


def test_the_module_still_exposes_the_default_connect():
    assert callable(postgres_module._default_connect)
