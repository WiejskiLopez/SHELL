"""Optimistic locking tests for Session aggregate."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pytest
from shell.domain.execution.aggregates.session.session import Session
from shell.domain.execution.aggregates.session.value_objects.session_id import SessionId
from shell.domain.platform.exceptions.concurrent_modification_error import (
    ConcurrentModificationError,
)
from shell.infrastructure.platform.persistence import SqlAlchemyUnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


_NOW = datetime(2024, 1, 1, 12, 0, 0)


class TestSessionOptimisticLocking:
    async def test_concurrent_modification_raises_error(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        uow1 = SqlAlchemyUnitOfWork(session_factory)
        uow2 = SqlAlchemyUnitOfWork(session_factory)

        async with uow1 as u:
            session = Session.open(id_=SessionId.generate(), now=_NOW)
            await u.session_repository.save(session)
            await u.commit()
            session_id = session.id

        async with uow1 as u1:
            entity_a = await u1.session_repository.get_by_id(session_id)
            assert entity_a is not None

            async with uow2 as u2:
                entity_b = await u2.session_repository.get_by_id(session_id)
                assert entity_b is not None

                entity_a.close(now=_NOW)
                await u1.session_repository.save(entity_a)
                await u1.commit()

                entity_b.close(now=_NOW)
                await u2.session_repository.save(entity_b)
                with pytest.raises(ConcurrentModificationError):
                    await u2.commit()
