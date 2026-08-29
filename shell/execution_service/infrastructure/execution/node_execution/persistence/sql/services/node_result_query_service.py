from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.execution_service.application.execution.node_execution.dto.node_execution_result import (
    NodeExecutionResultDto,
)
from shell.execution_service.infrastructure.execution.node_execution_state.persistence.sql.models.node_execution_state_aggregate import (
    NodeExecutionStateModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class NodeResultQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, node_execution_id: str) -> NodeExecutionResultDto | None:
        async with self._session_factory() as session:
            stmt = (
                select(NodeExecutionStateModel)
                .where(NodeExecutionStateModel.node_execution_id == node_execution_id)
                .where(NodeExecutionStateModel.direction == "OUT")
                .limit(1)
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            payload = model.state_data
            return NodeExecutionResultDto(
                id=model.id,
                node_execution_id=model.node_execution_id,
                workflow_id=_required_payload_field(payload, "workflow_id"),
                status=_required_payload_field(payload, "status"),
                stdout=_optional_payload_field(payload, "stdout"),
                stderr=_optional_payload_field(payload, "stderr"),
                artifact_uri=_optional_payload_field(payload, "artifact_uri"),
                created_at=model.created_at,
            )

    async def get_node_execution_result(
        self, node_execution_id: str, workflow_id: str
    ) -> NodeExecutionResultDto | None:
        async with self._session_factory() as session:
            stmt = (
                select(NodeExecutionStateModel)
                .where(NodeExecutionStateModel.node_execution_id == node_execution_id)
                .where(NodeExecutionStateModel.direction == "OUT")
                .limit(1)
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            payload = model.state_data
            return NodeExecutionResultDto(
                id=model.id,
                node_execution_id=model.node_execution_id,
                workflow_id=workflow_id,
                status=_required_payload_field(payload, "status"),
                stdout=_optional_payload_field(payload, "stdout"),
                stderr=_optional_payload_field(payload, "stderr"),
                artifact_uri=_optional_payload_field(payload, "artifact_uri"),
                created_at=model.created_at,
            )


def _required_payload_field(payload: object, field: str) -> str:
    value = payload.get(field) if isinstance(payload, dict) else None
    if value is None:
        from shell.platform.domain.exceptions import DomainError

        raise DomainError(f"Node result payload is missing required field '{field}'")
    return str(value)


def _optional_payload_field(payload: object, field: str) -> str | None:
    if not isinstance(payload, dict):
        return None
    value = payload.get(field)
    return str(value) if value is not None else None


__all__ = [
    "NodeResultQueryService",
]
