"""sql_driver.py
SqlDriver — abstract bridge between SqlMemoryBackend and a concrete SQL engine.

Slots:
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Sequence

from shell.memory.sql_driver.dialect import Dialect


class SqlDriver(ABC):
    """Abstract SQL driver used by SqlMemoryBackend.

    Implementations: SqliteDriver (default), PostgresDriver, future engines.
    """

    __slots__ = ()

    @property
    @abstractmethod
    def dialect_(self) -> Dialect:
        ...

    @abstractmethod
    def connect(self) -> None:
        ...

    @abstractmethod
    def close(self) -> None:
        ...

    @abstractmethod
    def execute(self, sql: str, params: Sequence[Any] = ()) -> None:
        ...

    @abstractmethod
    def executemany(self, sql: str, rows: Sequence[Sequence[Any]]) -> None:
        ...

    @abstractmethod
    def executescript(self, script: str) -> None:
        ...

    @abstractmethod
    def query(self, sql: str, params: Sequence[Any] = ()) -> list[dict]:
        ...

    @abstractmethod
    def last_insert_id(self) -> int:
        ...

    @abstractmethod
    def commit(self) -> None:
        ...
