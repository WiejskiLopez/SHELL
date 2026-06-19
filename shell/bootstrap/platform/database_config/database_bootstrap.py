from __future__ import annotations

from shell.infrastructure.platform.persistence.sql import create_all_tables, seed_base_data


async def bootstrap_database(url: str) -> None:
    await create_all_tables(url)
    await seed_base_data(url)
