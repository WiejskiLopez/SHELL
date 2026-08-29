from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from alembic import command
from alembic.config import Config

if TYPE_CHECKING:
    from pathlib import Path


def _run_upgrade(
    *,
    url: str,
    migrations_dir: Path,
    service_package: str,
    base_class: str,
    reset_db: bool,
) -> None:
    config = Config()
    config.set_main_option("script_location", str(migrations_dir))
    config.set_main_option("sqlalchemy.url", url.replace("+aiosqlite", "").replace("+asyncpg", ""))
    config.set_main_option("service_package", service_package)
    config.set_main_option("base_class", base_class)
    if reset_db:
        command.downgrade(config, "base")
    command.upgrade(config, "head")


async def run_versioned_migrations(
    *,
    url: str,
    migrations_dir: Path,
    service_package: str,
    base_class: str,
    reset_db: bool = False,
) -> None:
    await asyncio.to_thread(
        _run_upgrade,
        url=url,
        migrations_dir=migrations_dir,
        service_package=service_package,
        base_class=base_class,
        reset_db=reset_db,
    )
