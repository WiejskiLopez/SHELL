from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.application.platform.dto import EnvelopeDto
from shell.infrastructure.execution.persistence.sql.models import (
    EnvelopeModel
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class EnvelopeQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_envelopes_by_workflow(
        self, workflow_id: str, pending_only: bool = False
    ) -> list[EnvelopeDto]:
        async with self._session_factory() as session:
            stmt = select(EnvelopeModel).where(EnvelopeModel.workflow_id == workflow_id)
            if pending_only:
                stmt = stmt.where(EnvelopeModel.status == "pending")
            res = await session.execute(stmt)
            return [
                EnvelopeDto(
                    id=envelope_model.id,
                    workflow_id=envelope_model.workflow_id,
                    sender_graph_node_execution_id=envelope_model.sender_graph_node_execution_id,
                    receiver_graph_node_execution_id=envelope_model.receiver_graph_node_execution_id,
                    source_role=envelope_model.source_role,
                    target_role=envelope_model.target_role,
                    status=envelope_model.status,
                    stage=envelope_model.stage,
                    step=envelope_model.step,
                    payload=envelope_model.payload,
                    created_at=envelope_model.created_at,
                    updated_at=envelope_model.updated_at,
                )
                for envelope_model in res.scalars()
            ]
