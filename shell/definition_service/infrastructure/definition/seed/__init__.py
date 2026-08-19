"""Seed API for the Definition bounded context.

Each bounded context owns its seed data and exposes the same two public
operations through ``SeedProvider``: schema bootstrap (base/required data)
and development/demo data seeding. Both are idempotent.
"""

from __future__ import annotations

from shell.definition_service.infrastructure.definition.seed.base import seed_base_sync
from shell.definition_service.infrastructure.definition.seed.dev import seed_dev_sync
from shell.definition_service.migrations.baseline import run_definition_baseline
from shell.platform.application.ports.runtime.seed import SeedProvider
from shell.platform.infrastructure.persistence.sql.seed_helpers import run_seed_into


class DefinitionSeedProvider(SeedProvider):
    """Definition BC implementation of the platform ``SeedProvider`` contract."""

    async def bootstrap_database(self, url: str, reset_db: bool = False) -> None:
        await bootstrap_definition_database(url, reset_db)

    async def seed_dev_data(self, url: str) -> None:
        await seed_definition_dev_data(url)


async def bootstrap_definition_database(url: str, reset_db: bool = False) -> None:
    """Create the Definition schema and insert base/required data."""
    await run_definition_baseline(url, reset_db=reset_db)
    await run_seed_into(url, seed_base_sync)


async def seed_definition_dev_data(url: str, reset_db: bool = False) -> None:
    """Seed realistic development data for the Definition BC (idempotent)."""
    await bootstrap_definition_database(url, reset_db=reset_db)
    await run_seed_into(url, seed_dev_sync)


__all__ = [
    "DefinitionSeedProvider",
    "bootstrap_definition_database",
    "seed_definition_dev_data",
]
