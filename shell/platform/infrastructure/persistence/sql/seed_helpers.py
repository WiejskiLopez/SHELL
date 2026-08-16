"""Generic idempotent seeding helpers shared by bounded-context seeders."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy.engine import Connection


def seed_if_missing(
    session: Session,
    model: type[Any],
    record_id: str,
    builder: Callable[..., Any],
) -> Any:
    """Return the existing ``model`` row for ``record_id`` or insert a new one.

    When no row exists, ``builder()`` is invoked to create the instance and it
    is added to the session. Repeated calls never create duplicates.
    """
    existing = session.execute(select(model).where(model.id == record_id)).scalar_one_or_none()
    if existing is not None:
        return existing
    instance = builder()
    session.add(instance)
    return instance


async def run_seed_into(url: str, seed_fn: Callable[[Session], None]) -> None:
    """Run a synchronous seed function against the database at ``url``.

    Every bounded-context seed reuses the same engine lifecycle: a single
    connection owns one session, the seed function runs inside it and the
    session commits at the end.
    """
    engine = create_async_engine(url, echo=False, future=True)
    async with engine.begin() as connection:
        await connection.run_sync(_run_sync_seed, seed_fn)
    await engine.dispose()


def _run_sync_seed(sync_conn: Connection, seed_fn: Callable[[Session], None]) -> None:
    session = Session(sync_conn)
    seed_fn(session)
    session.commit()


__all__ = ["run_seed_into", "seed_if_missing"]
