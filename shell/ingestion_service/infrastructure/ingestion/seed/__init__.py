"""Seed API for the Ingestion bounded context.

Each bounded context owns its seed data and exposes the same two public
operations through ``SeedProvider``: schema bootstrap (base/required data)
and development/demo data seeding. Both are idempotent.
"""

from __future__ import annotations

from shell.ingestion_service.infrastructure.ingestion.seed.dev import seed_dev_sync
from shell.ingestion_service.migrations.baseline import run_ingestion_baseline
from shell.platform.application.ports.seed import SeedProvider
from shell.platform.infrastructure.persistence.sql.seed_helpers import run_seed_into


class IngestionSeedProvider(SeedProvider):
    """Ingestion BC implementation of the platform ``SeedProvider`` contract."""

    async def bootstrap_database(self, url: str, reset_db: bool = False) -> None:
        await bootstrap_ingestion_database(url, reset_db)

    async def seed_dev_data(self, url: str) -> None:
        await seed_ingestion_dev_data(url)


async def bootstrap_ingestion_database(url: str, reset_db: bool = False) -> None:
    """Create the Ingestion schema (base data is not required for this BC)."""
    await run_ingestion_baseline(url, reset_db=reset_db)


async def seed_ingestion_dev_data(url: str, reset_db: bool = False) -> None:
    """Seed realistic development data for the Ingestion BC (idempotent)."""
    await bootstrap_ingestion_database(url, reset_db=reset_db)
    await run_seed_into(url, seed_dev_sync)


__all__ = [
    "IngestionSeedProvider",
    "bootstrap_ingestion_database",
    "seed_ingestion_dev_data",
]
