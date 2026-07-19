"""Debug repository path optimistic locking."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from shell.domain.execution.aggregates.workflow.repositories.workflow_repository import (
    WorkflowRepository,
)
from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
from shell.domain.execution.aggregates.workflow.workflow import Workflow
from shell.platform.domain.exceptions.concurrent_modification_error import (
    ConcurrentModificationError,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.infrastructure.persistence import SqlAlchemyUnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


class TestRepoDebug:
    async def test_debug(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        import uuid

        wf_id = WorkflowId(str(uuid.uuid4()))
        now = CreatedAt.from_datetime(datetime(2024, 1, 1, tzinfo=UTC))

        wf = Workflow.create(id_=wf_id, now=now)

        uow_a = SqlAlchemyUnitOfWork(session_factory)
        uow_b = SqlAlchemyUnitOfWork(session_factory)

        async with uow_a as ua:
            await ua.repository(WorkflowRepository).save(wf)
            await ua.commit()

        async with uow_a as ua:
            loaded = await ua.repository(WorkflowRepository).get_by_id(wf_id)
            assert loaded is not None
            loaded.finish()
            await ua.repository(WorkflowRepository).save(loaded)

            async with uow_b as ub:
                loaded2 = await ub.repository(WorkflowRepository).get_by_id(wf_id)
                assert loaded2 is not None
                loaded2.abort(reason="concurrent")
                await ub.repository(WorkflowRepository).save(loaded2)

                await ua.commit()

                with pytest.raises(ConcurrentModificationError):
                    await ub.commit()
