"""Test lifecycle — track SQL session factories for explicit engine disposal.

``make_*_app`` helpers construct a per-test container whose ``build_session_factory``
engine would otherwise be recycled by the garbage collector (SAWarning about
non-checked-in connections).  Every factory created inside a test is registered
here and disposed by an autouse root fixture after the test completes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from shell.platform.infrastructure.persistence.sql import dispose_session_factory

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

_session_factories: list[async_sessionmaker[AsyncSession]] = []


def track_session_factory(session_factory: async_sessionmaker[AsyncSession]) -> None:
    _session_factories.append(session_factory)


@pytest.fixture(autouse=True)
async def dispose_tracked_session_factories() -> AsyncGenerator[None, None]:
    yield
    while _session_factories:
        session_factory = _session_factories.pop()
        await dispose_session_factory(session_factory)


__all__ = ["track_session_factory", "dispose_tracked_session_factories"]
