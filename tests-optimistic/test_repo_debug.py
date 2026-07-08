"""Debug repository path optimistic locking."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

_NOW = datetime(2024, 1, 1)


class TestRepoDebug:
    async def test_debug(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        import uuid

        from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
        from shell.domain.execution.aggregates.workflow.workflow import Workflow
        from shell.domain.platform.exceptions.concurrent_modification_error import (
            ConcurrentModificationError,
        )
        from shell.infrastructure.execution.workflow.persistence.sql.models import WorkflowModel
        from shell.infrastructure.platform.persistence import SqlAlchemyUnitOfWork

        wf_id = str(uuid.uuid4())

        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            model = WorkflowModel(id=wf_id, status="active", created_at=_NOW)
            uow._active_session.add(model)
            await uow.commit()

        uow_a = SqlAlchemyUnitOfWork(session_factory)
        uow_b = SqlAlchemyUnitOfWork(session_factory)

        async with uow_a as ua:
            ea = Workflow(
                id=WorkflowId(wf_id),
                status="active",
                created_at=_NOW,
            )
            await ua.workflow_repository.save(ea)

            async with uow_b as ub:
                eb = Workflow(
                    id=WorkflowId(wf_id),
                    status="active",
                    created_at=_NOW,
                )
                await ub.workflow_repository.save(eb)

                ea.finish(now=_NOW)
                await ua.workflow_repository.save(ea)
                await ua.commit()

                eb.abort(reason="concurrent", now=_NOW)
                await ub.workflow_repository.save(eb)
                with pytest.raises(ConcurrentModificationError):
                    await ub.commit()
