"""Seed API for the Execution bounded context.

Each bounded context owns its seed data and exposes the same two public
operations through ``SeedProvider``: schema bootstrap (base/required data)
and development/demo data seeding. Both are idempotent.
"""

from __future__ import annotations

from shell.execution_service.infrastructure.execution.seed.dev import seed_dev_sync
from shell.execution_service.migrations.baseline import run_execution_baseline
from shell.platform.application.ports.runtime.seed import SeedProvider
from shell.platform.infrastructure.persistence.sql.seed_helpers import run_seed_into


class ExecutionSeedProvider(SeedProvider):
    """Execution BC implementation of the platform ``SeedProvider`` contract."""

    async def bootstrap_database(self, url: str, reset_db: bool = False) -> None:
        await bootstrap_execution_database(url, reset_db)

    async def seed_dev_data(self, url: str) -> None:
        await seed_execution_dev_data(url)


async def bootstrap_execution_database(url: str, reset_db: bool = False) -> None:
    """Create the Execution schema (base data is not required for this BC)."""
    await run_execution_baseline(url, reset_db=reset_db)


async def seed_execution_dev_data(url: str, reset_db: bool = False) -> None:
    """Seed realistic development data for the Execution BC (idempotent)."""
    await bootstrap_execution_database(url, reset_db=reset_db)
    await run_seed_into(url, seed_dev_sync)


__all__ = [
    "ExecutionSeedProvider",
    "bootstrap_execution_database",
    "seed_execution_dev_data",
]
