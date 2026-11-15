"""A Postgres run queue for multi-replica deployments.

Claims use ``FOR UPDATE SKIP LOCKED`` so several service pods can share one
queue without a broker; the optional ``psycopg`` dependency is imported lazily.
"""

import json
import uuid
from collections.abc import Callable
from datetime import datetime, timezone

from .store import Run, StoreError, _canonical_json

_RUN_COLUMNS = (
    "id, bundle, status, created_at, started_at, finished_at, exit, report,"
    " error, idempotency_key, attempts, cancel_requested"
)

_RUNS_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    bundle TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    exit INTEGER,
    report JSONB,
    error TEXT,
    idempotency_key TEXT UNIQUE,
    attempts INTEGER NOT NULL DEFAULT 0,
    cancel_requested BOOLEAN NOT NULL DEFAULT FALSE
)
"""

_EVENTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id BIGSERIAL PRIMARY KEY,
    delivery TEXT UNIQUE,
    event TEXT NOT NULL,
    action TEXT,
    installation TEXT,
    received_at TIMESTAMPTZ NOT NULL,
    payload JSONB
)
"""

_RUNS_INDEX = """
CREATE INDEX IF NOT EXISTS runs_queue_idx ON runs (status, created_at)
"""


def _default_connect(dsn: str):
    try:
        import psycopg
    except ImportError as error:
        raise StoreError(
            "postgres support requires the optional dependency:"
            " pip install 'tenonhq[postgres]'"
        ) from error
    return psycopg.connect(dsn, autocommit=True)


def _stamp(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _load_json(value: object) -> dict | None:
    if value is None:
        return None
    if isinstance(value, str):
        return json.loads(value)
    return value  # type: ignore[return-value]


def _row_to_run(row) -> Run:
    return Run(
        id=row[0],
        bundle=row[1],
        status=row[2],
        created_at=_stamp(row[3]),
        started_at=_stamp(row[4]),
        finished_at=_stamp(row[5]),
        exit=row[6],
        report=_load_json(row[7]),
        error=row[8],
        idempotency_key=row[9],
        attempts=row[10],
        cancel_requested=bool(row[11]),
    )


class PostgresRunStore:
    """The shared Postgres queue; every statement is atomic on its own."""

    def __init__(
        self,
        dsn: str,
        *,
        connect: Callable[[str], object] | None = None,
        now: Callable[[], datetime] | None = None,
        new_id: Callable[[], str] | None = None,
    ) -> None:
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._new_id = new_id or (lambda: uuid.uuid4().hex)
        connector = connect or _default_connect
        try:
            self._connection = connector(dsn)
        except StoreError:
            raise
        except Exception as error:  # noqa: BLE001 - any connect failure is named
            raise StoreError(f"cannot connect to postgres: {error}") from error
        try:
            self._execute(_RUNS_SCHEMA)
            self._execute(_EVENTS_SCHEMA)
            self._execute(_RUNS_INDEX)
        except Exception as error:  # noqa: BLE001 - any schema failure is named
            raise StoreError(f"cannot open the postgres store: {error}") from error

    def _execute(self, sql: str, params: tuple | None = None):
        if params is None:
            return self._connection.execute(sql)
        return self._connection.execute(sql, params)

    def create_run(
        self, bundle: str, idempotency_key: str | None = None
    ) -> Run:
        if idempotency_key is not None:
            existing = self.find_by_idempotency_key(idempotency_key)
            if existing is not None:
                return existing
        now = self._now()
        run = Run(
            id=self._new_id(),
            bundle=bundle,
            status="queued",
            created_at=now.isoformat(),
            idempotency_key=idempotency_key,
        )
        self._execute(
            "INSERT INTO runs (id, bundle, status, created_at,"
            " idempotency_key) VALUES (%s, %s, %s, %s, %s)"
            " ON CONFLICT (idempotency_key) DO NOTHING",
            (run.id, run.bundle, run.status, now, run.idempotency_key),
        )
        # Spec AC3: a concurrent writer may have won the key; read the winner.
        if idempotency_key is not None:
            existing = self.find_by_idempotency_key(idempotency_key)
            if existing is not None:
                return existing
        return run

    # Spec AC2: one statement locks and claims the oldest row; peers skip it.
    def claim_next(self) -> Run | None:
        row = self._execute(
            "WITH next AS ("
            " SELECT id FROM runs WHERE status = 'queued'"
            " ORDER BY created_at, id FOR UPDATE SKIP LOCKED LIMIT 1"
            ") UPDATE runs SET status = 'running', started_at = %s,"
            " attempts = attempts + 1 FROM next WHERE runs.id = next.id"
            f" RETURNING {_RUN_COLUMNS}",
            (self._now(),),
        ).fetchone()
        return None if row is None else _row_to_run(row)

    def requeue(self, run_id: str) -> Run:
        row = self._get(run_id)
        if row is None:
            raise ValueError(f"unknown run: {run_id}")
        if row.status != "running":
            raise ValueError(f"run {run_id} is {row.status}, not running")
        self._execute(
            "UPDATE runs SET status = 'queued', started_at = NULL,"
            " finished_at = NULL, exit = NULL, report = NULL, error = NULL"
            " WHERE id = %s AND status = 'running'",
            (run_id,),
        )
        return self.get(run_id)  # type: ignore[return-value]

    def finish(
        self,
        run_id: str,
        *,
        status: str,
        exit: int,
        report: dict | None,
        error: str | None = None,
    ) -> Run:
        if status not in ("succeeded", "failed", "cancelled"):
            raise ValueError(f"invalid finish status: {status}")
        row = self._get(run_id)
        if row is None:
            raise ValueError(f"unknown run: {run_id}")
        if row.status != "running":
            raise ValueError(f"run {run_id} is {row.status}, not running")
        self._execute(
            "UPDATE runs SET status = %s, finished_at = %s, exit = %s,"
            " report = %s::jsonb, error = %s"
            " WHERE id = %s AND status = 'running'",
            (
                status,
                self._now(),
                exit,
                None if report is None else _canonical_json(report),
                error,
                run_id,
            ),
        )
        return self.get(run_id)  # type: ignore[return-value]

    # Spec AC3: queued runs cancel now; running runs get the worker flag.
    def request_cancel(self, run_id: str) -> Run | None:
        row = self._get(run_id)
        if row is None:
            return None
        if row.status == "queued":
            self._execute(
                "UPDATE runs SET status = 'cancelled', finished_at = %s"
                " WHERE id = %s AND status = 'queued'",
                (self._now(), run_id),
            )
        elif row.status == "running":
            self._execute(
                "UPDATE runs SET cancel_requested = TRUE"
                " WHERE id = %s AND status = 'running'",
                (run_id,),
            )
        return self.get(run_id)

    def cancel_requested(self, run_id: str) -> bool:
        row = self._execute(
            "SELECT cancel_requested FROM runs WHERE id = %s", (run_id,)
        ).fetchone()
        return row is not None and bool(row[0])

    # Spec AC3: a multi-replica recovery only touches rows past the lease.
    def recover(self, older_than: datetime | None = None) -> int:
        cancelled = self._execute(
            "UPDATE runs SET status = 'cancelled', finished_at = %s"
            " WHERE status = 'running' AND cancel_requested RETURNING id",
            (self._now(),),
        ).fetchall()
        sql = (
            "UPDATE runs SET status = 'queued', started_at = NULL"
            " WHERE status = 'running' AND NOT cancel_requested"
        )
        params = None
        if older_than is not None:
            sql += " AND (started_at IS NULL OR started_at < %s)"
            params = (older_than,)
        requeued = self._execute(sql + " RETURNING id", params).fetchall()
        return len(cancelled) + len(requeued)

    def counts(self) -> dict[str, int]:
        counts = dict.fromkeys(
            ("queued", "running", "succeeded", "failed", "cancelled"), 0
        )
        rows = self._execute(
            "SELECT status, COUNT(*) FROM runs GROUP BY status"
        ).fetchall()
        for status, total in rows:
            counts[status] = total
        return counts

    def get(self, run_id: str) -> Run | None:
        return self._get(run_id)

    def find_by_idempotency_key(self, key: str | None) -> Run | None:
        row = self._execute(
            f"SELECT {_RUN_COLUMNS} FROM runs WHERE idempotency_key = %s",
            (key,),
        ).fetchone()
        return None if row is None else _row_to_run(row)

    def list(self, limit: int = 50) -> tuple[Run, ...]:
        limit = max(1, min(limit, 200))
        rows = self._execute(
            f"SELECT {_RUN_COLUMNS} FROM runs"
            " ORDER BY created_at DESC, id DESC LIMIT %s",
            (limit,),
        ).fetchall()
        return tuple(_row_to_run(row) for row in rows)

    def record_event(
        self,
        delivery: str,
        event: str,
        action: str | None = None,
        installation: str | None = None,
        payload: dict | None = None,
    ) -> bool:
        row = self._execute(
            "INSERT INTO events (delivery, event, action, installation,"
            " payload, received_at) VALUES (%s, %s, %s, %s, %s::jsonb, %s)"
            " ON CONFLICT (delivery) DO NOTHING RETURNING id",
            (
                delivery,
                event,
                action,
                installation,
                None if payload is None else _canonical_json(payload),
                self._now(),
            ),
        ).fetchone()
        return row is not None

    def _get(self, run_id: str) -> Run | None:
        row = self._execute(
            f"SELECT {_RUN_COLUMNS} FROM runs WHERE id = %s", (run_id,)
        ).fetchone()
        return None if row is None else _row_to_run(row)

    # Spec AC3: a schema read, not just the connection.
    def ping(self) -> bool:
        try:
            self._execute("SELECT 1 FROM runs LIMIT 1").fetchall()
        except Exception:  # noqa: BLE001 - the driver's error type is optional
            return False
        return True

    def close(self) -> None:
        self._connection.close()
