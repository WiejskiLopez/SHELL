"""Adaptery repozytoriów sag (SQL, InMemory — fakes)."""

from shell.platform.infrastructure.process.saga.repositories.sql_saga_repository import (
    SqlSagaRepository,
)

__all__ = [
    "SqlSagaRepository",
]
