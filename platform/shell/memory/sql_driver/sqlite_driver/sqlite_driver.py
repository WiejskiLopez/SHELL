"""sqlite_driver.py
SqliteDriver — SQLite implementation of SqlDriver (sqlite3, stdlib).

Slots:
    _db_path    — filesystem path to the SQLite database file
    _connection — Optional; sqlite3.Connection (None until connect)
    _dialect    — Dialect describing SQLite SQL specifics
"""

from __future__ import annotations

import sqlite3
from typing import Any, Sequence

from shell.utils.path.path import Path, PathType
from shell.memory.sql_driver.sql_driver import SqlDriver
from shell.memory.sql_driver.dialect import Dialect


_SQLITE_DIALECT = Dialect(
    placeholder="?",
    auto_pk="INTEGER PRIMARY KEY AUTOINCREMENT",
    blob_type="BLOB",
    supports_fts=True,
)


class SqliteDriver(SqlDriver):
    """SQLite SqlDriver."""

    __slots__ = ("_db_path", "_connection", "_dialect")

    def __init__(self, db_path: PathType) -> None:
        self._db_path: PathType = db_path
        self._connection: sqlite3.Connection | None = None
        self._dialect: Dialect = _SQLITE_DIALECT

    @property
    def dialect_(self) -> Dialect:
        return self._dialect

    @property
    def db_path_(self) -> PathType:
        return self._db_path

    @property
    def connection_(self) -> sqlite3.Connection:
        return self._connection

    def connect(self) -> None:
        parent = self._db_path.parent
        if not Path.exists(parent):
            Path.mkdir(parent)
        self._connection = sqlite3.connect(str(self._db_path), timeout=30.0)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._connection.execute("PRAGMA synchronous = NORMAL")
        self._connection.execute("PRAGMA busy_timeout = 5000")

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def execute(self, sql: str, params: Sequence[Any] = ()) -> None:
        self._connection.execute(self._dialect.render_sql(sql), tuple(params))

    def executemany(self, sql: str, rows: Sequence[Sequence[Any]]) -> None:
        self._connection.executemany(self._dialect.render_sql(sql), [tuple(r) for r in rows])

    def executescript(self, script: str) -> None:
        self._connection.executescript(script)

    def query(self, sql: str, params: Sequence[Any] = ()) -> list[dict]:
        cursor = self._connection.execute(self._dialect.render_sql(sql), tuple(params))
        return [dict(row) for row in cursor.fetchall()]

    def last_insert_id(self) -> int:
        row = self._connection.execute("SELECT last_insert_rowid() AS id").fetchone()
        return int(row["id"]) if row else 0

    def commit(self) -> None:
        self._connection.commit()
