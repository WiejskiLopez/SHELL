"""Versioned schema migrations for the Session bounded context."""

from __future__ import annotations

import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config

_MIGRATIONS_DIR = Path(__file__).resolve().parent


def _sync_database_url(url: str) -> str:
    return url.replace("+aiosqlite", "").replace("+asyncpg", "")


def _upgrade(url: str, reset_db: bool) -> None:
    config = Config()
    config.set_main_option("script_location", str(_MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", _sync_database_url(url))
    if reset_db:
        command.downgrade(config, "base")
    command.upgrade(config, "head")


async def run_session_baseline(url: str, reset_db: bool = False) -> None:
    """Apply the standalone Session migration history up to ``head``."""
    await asyncio.to_thread(_upgrade, url, reset_db)
