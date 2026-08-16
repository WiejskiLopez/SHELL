"""Generic helpers for verifying per-BC seed idempotency."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import create_async_engine


async def count_rows(url: str, model: type[Any]) -> int:
    """Return the number of rows in the table mapped to ``model``."""
    engine = create_async_engine(url, future=True)
    async with engine.connect() as connection:
        result = await connection.execute(select(func.count()).select_from(model.__table__))
        count = result.scalar_one()
    await engine.dispose()
    return count


__all__ = ["count_rows"]
