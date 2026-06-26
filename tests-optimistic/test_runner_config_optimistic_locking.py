"""Optimistic locking tests for RunnerConfig entity."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pytest
from shell.domain.definition.entities.runner_config import RunnerConfig
from shell.domain.definition.value_objects.ids import RunnerConfigId
from shell.domain.platform.exceptions.concurrent_modification_error import (
    ConcurrentModificationError,
)
from shell.domain.platform.value_objects.hash import Hash
from shell.infrastructure.platform.persistence import SqlAlchemyUnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


_NOW = datetime(2024, 1, 1, 12, 0, 0)


class TestRunnerConfigOptimisticLocking:
    async def test_concurrent_modification_raises_error(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        uow1 = SqlAlchemyUnitOfWork(session_factory)
        uow2 = SqlAlchemyUnitOfWork(session_factory)
        rc_id = RunnerConfigId.generate()

        async with uow1 as u:
            entity = RunnerConfig.new(
                id_=rc_id,
                package_name="pkg-v1",
                kind="python",
                body={"key": "v1"},
                config_hash=Hash.of("v1"),
                now=_NOW,
            )
            await u.runner_config_repository.save(entity)
            await u.commit()

        async with uow1 as u1:
            entity_a = await u1.runner_config_repository.get_by_id(rc_id)
            assert entity_a is not None

            async with uow2 as u2:
                entity_b = await u2.runner_config_repository.get_by_id(rc_id)
                assert entity_b is not None

                modified_a = RunnerConfig.new(
                    id_=rc_id,
                    package_name="pkg-v2",
                    kind="python",
                    body={"key": "v2"},
                    config_hash=Hash.of("v2"),
                    now=_NOW,
                )
                await u1.runner_config_repository.save(modified_a)
                await u1.commit()

                modified_b = RunnerConfig.new(
                    id_=rc_id,
                    package_name="pkg-v3",
                    kind="python",
                    body={"key": "v3"},
                    config_hash=Hash.of("v3"),
                    now=_NOW,
                )
                await u2.runner_config_repository.save(modified_b)
                with pytest.raises(ConcurrentModificationError):
                    await u2.commit()
