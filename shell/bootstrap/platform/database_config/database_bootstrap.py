from __future__ import annotations

from shell.infrastructure.platform.persistence.sql import run_migrations, seed_base_data


async def bootstrap_database(url: str) -> None:
    await run_migrations(url)
    await seed_base_data(url)
