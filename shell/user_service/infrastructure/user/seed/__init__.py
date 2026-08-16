"""Seed API for the User bounded context.

Each bounded context owns its seed data and exposes the same two public
operations through ``SeedProvider``: schema bootstrap (base/required data)
and development/demo data seeding. Both are idempotent.
"""

from __future__ import annotations

from shell.platform.application.ports.seed import SeedProvider
from shell.platform.infrastructure.persistence.sql.seed_helpers import run_seed_into
from shell.user_service.infrastructure.user.seed.dev import seed_dev_sync
from shell.user_service.migrations.baseline import run_user_baseline


class UserSeedProvider(SeedProvider):
    """User BC implementation of the platform ``SeedProvider`` contract."""

    async def bootstrap_database(self, url: str, reset_db: bool = False) -> None:
        await bootstrap_user_database(url, reset_db)

    async def seed_dev_data(self, url: str) -> None:
        await seed_user_dev_data(url)


async def bootstrap_user_database(url: str, reset_db: bool = False) -> None:
    """Create the User schema (base data is not required for this BC)."""
    await run_user_baseline(url, reset_db=reset_db)


async def seed_user_dev_data(url: str, reset_db: bool = False) -> None:
    """Seed realistic development data for the User BC (idempotent)."""
    await bootstrap_user_database(url, reset_db=reset_db)
    await run_seed_into(url, seed_dev_sync)


__all__ = [
    "UserSeedProvider",
    "bootstrap_user_database",
    "seed_user_dev_data",
]
