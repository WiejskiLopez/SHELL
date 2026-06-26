"""Optimistic locking tests for Envelope aggregate."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pytest
from shell.domain.execution.aggregates.envelope.envelope import Envelope
from shell.domain.execution.aggregates.envelope.value_objects.envelope_id import EnvelopeId
from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
from shell.domain.platform.exceptions.concurrent_modification_error import (
    ConcurrentModificationError,
)
from shell.domain.platform.value_objects.envelope_status import EnvelopeStatus
from shell.infrastructure.platform.persistence import SqlAlchemyUnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker


_NOW = datetime(2024, 1, 1, 12, 0, 0)


class TestEnvelopeOptimisticLocking:
    async def test_concurrent_modification_raises_error(
        self,
        session_factory: async_sessionmaker,
    ) -> None:
        uow1 = SqlAlchemyUnitOfWork(session_factory)
        uow2 = SqlAlchemyUnitOfWork(session_factory)

        async with uow1 as u:
            envelope = Envelope.new(
                id_=EnvelopeId.generate(),
                workflow_id=WorkflowId.generate(),
                sender_graph_node_execution_id=GraphNodeExecutionId.generate(),
                receiver_graph_node_execution_id=GraphNodeExecutionId.generate(),
                source_role="agent",
                target_role="router",
                now=_NOW,
            )
            await u.envelope_repository.save(envelope)
            await u.commit()
            envelope_id = envelope.id

        async with uow1 as u1:
            entity_a = await u1.envelope_repository.get_by_id(envelope_id)
            assert entity_a is not None

            async with uow2 as u2:
                entity_b = await u2.envelope_repository.get_by_id(envelope_id)
                assert entity_b is not None

                entity_a.transition_status(EnvelopeStatus.ACTIVE, now=_NOW)
                await u1.envelope_repository.save(entity_a)
                await u1.commit()

                entity_b.transition_status(EnvelopeStatus.ACTIVE, now=_NOW)
                await u2.envelope_repository.save(entity_b)
                with pytest.raises(ConcurrentModificationError):
                    await u2.commit()
