from __future__ import annotations

import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config

_PLATFORM_MIGRATIONS_DIR: Path | None = None


def _platform_migrations_dir() -> Path:
    global _PLATFORM_MIGRATIONS_DIR
    if _PLATFORM_MIGRATIONS_DIR is None:
        _PLATFORM_MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations" / "sql"
    return _PLATFORM_MIGRATIONS_DIR


def _run_upgrade(
    *,
    url: str,
    migrations_dir: Path,
    service_package: str,
    base_class: str,
    reset_db: bool,
    include_saga: bool,
) -> None:
    config = Config()
    config.set_main_option("script_location", str(migrations_dir))
    config.set_main_option("sqlalchemy.url", url.replace("+aiosqlite", "").replace("+asyncpg", ""))
    config.set_main_option("service_package", service_package)
    config.set_main_option("base_class", base_class)
    config.set_main_option("include_saga", str(include_saga).lower())
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
        include_saga=True,
    )


async def run_platform_baseline(
    *, url: str, reset_db: bool = False, include_saga: bool = False
) -> None:
    """Apply the shared platform delivery-migrations chain (``platform_0001_..``)."""
    await asyncio.to_thread(
        _run_upgrade,
        url=url,
        migrations_dir=_platform_migrations_dir(),
        service_package="",
        base_class="",
        reset_db=reset_db,
        include_saga=include_saga,
    )
