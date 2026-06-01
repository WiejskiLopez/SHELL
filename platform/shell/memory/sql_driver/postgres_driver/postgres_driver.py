"""postgres_driver.py
PostgresDriver — PostgreSQL stub implementation of SqlDriver.

Wymaga psycopg / psycopg2 (nie zainstalowane domyślnie). Stub do podpięcia
gdy projekt zdecyduje się na Postgres.

Slots:
    _dsn        — connection string ('postgresql://user:pass@host:port/db')
    _connection — Optional; psycopg connection (None until connect)
    _dialect    — Dialect describing Postgres SQL specifics
"""

from __future__ import annotations

from typing import Any, Sequence

from shell.memory.sql_driver.sql_driver import SqlDriver
from shell.memory.sql_driver.dialect import Dialect


_POSTGRES_DIALECT = Dialect(
    placeholder="%s",
    auto_pk="BIGSERIAL PRIMARY KEY",
    blob_type="BYTEA",
    supports_fts=False,
)


class PostgresDriver(SqlDriver):
    """PostgreSQL SqlDriver (stub)."""

    __slots__ = ("_dsn", "_connection", "_dialect")

    def __init__(self, dsn: str) -> None:
        self._dsn: str = dsn
        self._connection = None
        self._dialect: Dialect = _POSTGRES_DIALECT

    @property
    def dialect_(self) -> Dialect:
        return self._dialect

    @property
    def dsn_(self) -> str:
        return self._dsn

    def connect(self) -> None:
        raise NotImplementedError("[PostgresDriver] psycopg integration not implemented yet")

    def close(self) -> None:
        raise NotImplementedError("[PostgresDriver] psycopg integration not implemented yet")

    def execute(self, sql: str, params: Sequence[Any] = ()) -> None:
        raise NotImplementedError("[PostgresDriver] psycopg integration not implemented yet")

    def executemany(self, sql: str, rows: Sequence[Sequence[Any]]) -> None:
        raise NotImplementedError("[PostgresDriver] psycopg integration not implemented yet")

    def executescript(self, script: str) -> None:
        raise NotImplementedError("[PostgresDriver] psycopg integration not implemented yet")

    def query(self, sql: str, params: Sequence[Any] = ()) -> list[dict]:
        raise NotImplementedError("[PostgresDriver] psycopg integration not implemented yet")

    def last_insert_id(self) -> int:
        raise NotImplementedError("[PostgresDriver] psycopg integration not implemented yet")

    def commit(self) -> None:
        raise NotImplementedError("[PostgresDriver] psycopg integration not implemented yet")
