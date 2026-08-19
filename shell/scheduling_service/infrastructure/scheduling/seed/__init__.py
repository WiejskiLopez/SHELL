"""Seed API for the Scheduling bounded context.

Each bounded context owns its seed data and exposes the same two public
operations through ``SeedProvider``: schema bootstrap (base/required data)
and development/demo data seeding. Both are idempotent.
"""

from __future__ import annotations

from shell.platform.application.ports.runtime.seed import SeedProvider
from shell.platform.infrastructure.persistence.sql.seed_helpers import run_seed_into
from shell.scheduling_service.infrastructure.scheduling.seed.dev import seed_dev_sync
from shell.scheduling_service.migrations.baseline import run_scheduling_baseline


class SchedulingSeedProvider(SeedProvider):
    """Scheduling BC implementation of the platform ``SeedProvider`` contract."""

    async def bootstrap_database(self, url: str, reset_db: bool = False) -> None:
        await bootstrap_scheduling_database(url, reset_db)

    async def seed_dev_data(self, url: str) -> None:
        await seed_scheduling_dev_data(url)


async def bootstrap_scheduling_database(url: str, reset_db: bool = False) -> None:
    """Create the Scheduling schema (base data is not required for this BC)."""
    await run_scheduling_baseline(url, reset_db=reset_db)


async def seed_scheduling_dev_data(url: str, reset_db: bool = False) -> None:
    """Seed realistic development data for the Scheduling BC (idempotent)."""
    await bootstrap_scheduling_database(url, reset_db=reset_db)
    await run_seed_into(url, seed_dev_sync)


__all__ = [
    "SchedulingSeedProvider",
    "bootstrap_scheduling_database",
    "seed_scheduling_dev_data",
]
