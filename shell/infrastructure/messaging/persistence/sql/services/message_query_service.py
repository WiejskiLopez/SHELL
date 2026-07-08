from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.application.messaging.dto.message import MessageDto
from shell.infrastructure.messaging.persistence.sql.models.message import MessageModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class MessageQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, message_id: str) -> MessageDto | None:
        async with self._session_factory() as session:
            stmt = select(MessageModel).where(MessageModel.id == message_id)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return MessageDto(
                id=model.id,
                message_type=model.message_type,
                business_payload=model.business_payload,
                metadata=model.message_metadata,
                source=model.source,
                destination=model.destination,
                status=model.status,
                workflow_id=model.workflow_id,
                step=model.step,
                sequence_id=model.sequence_id,
                source_node_execution_id=model.source_node_execution_id,
                target_node_execution_id=model.target_node_execution_id,
                source_role=model.source_role,
                target_role=model.target_role,
                created_at=model.created_at,
                received_at=model.received_at,
            )

    async def list_by_workflow_id(self, workflow_id: str) -> list[MessageDto]:
        async with self._session_factory() as session:
            stmt = select(MessageModel).where(MessageModel.workflow_id == workflow_id)
            res = await session.execute(stmt)
            return [
                MessageDto(
                    id=model.id,
                    message_type=model.message_type,
                    business_payload=model.business_payload,
                    metadata=model.message_metadata,
                    source=model.source,
                    destination=model.destination,
                    status=model.status,
                    workflow_id=model.workflow_id,
                    step=model.step,
                    sequence_id=model.sequence_id,
                    source_node_execution_id=model.source_node_execution_id,
                    target_node_execution_id=model.target_node_execution_id,
                    source_role=model.source_role,
                    target_role=model.target_role,
                    created_at=model.created_at,
                    received_at=model.received_at,
                )
                for model in res.scalars()
            ]

    async def list_by_source(self, source: str) -> list[MessageDto]:
        async with self._session_factory() as session:
            stmt = select(MessageModel).where(MessageModel.source == source)
            res = await session.execute(stmt)
            return [
                MessageDto(
                    id=model.id,
                    message_type=model.message_type,
                    business_payload=model.business_payload,
                    metadata=model.message_metadata,
                    source=model.source,
                    destination=model.destination,
                    status=model.status,
                    workflow_id=model.workflow_id,
                    step=model.step,
                    sequence_id=model.sequence_id,
                    source_node_execution_id=model.source_node_execution_id,
                    target_node_execution_id=model.target_node_execution_id,
                    source_role=model.source_role,
                    target_role=model.target_role,
                    created_at=model.created_at,
                    received_at=model.received_at,
                )
                for model in res.scalars()
            ]

    async def list_by_destination(self, destination: str) -> list[MessageDto]:
        async with self._session_factory() as session:
            stmt = select(MessageModel).where(MessageModel.destination == destination)
            res = await session.execute(stmt)
            return [
                MessageDto(
                    id=model.id,
                    message_type=model.message_type,
                    business_payload=model.business_payload,
                    metadata=model.message_metadata,
                    source=model.source,
                    destination=model.destination,
                    status=model.status,
                    workflow_id=model.workflow_id,
                    step=model.step,
                    sequence_id=model.sequence_id,
                    source_node_execution_id=model.source_node_execution_id,
                    target_node_execution_id=model.target_node_execution_id,
                    source_role=model.source_role,
                    target_role=model.target_role,
                    created_at=model.created_at,
                    received_at=model.received_at,
                )
                for model in res.scalars()
            ]


__all__ = [
    "MessageQueryService",
]
