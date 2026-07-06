from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
    NodeExecutionId,
)
from shell.domain.execution.aggregates.node_execution_state.node_execution_state import (
    NodeExecutionState,
)
from shell.domain.execution.aggregates.node_execution_state.repositories.node_execution_state_repository import (
    NodeExecutionStateRepository,
)
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.exists_result import ExistsResult
from shell.domain.platform.value_objects.state_data import StateData
from shell.domain.platform.value_objects.state_direction import StateDirection
from shell.infrastructure.execution.node_execution_state.persistence.sql.models.node_execution_state_aggregate import (
    NodeExecutionStateModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


from shell.domain.execution.aggregates.node_execution_state.value_objects.node_execution_state_id import (
    NodeExecutionStateId,
)


class SqlNodeExecutionStateRepository(NodeExecutionStateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id_: object) -> NodeExecutionState | None:
        id_value = id_.value if hasattr(id_, "value") else id_
        model = await self._session.get(NodeExecutionStateModel, id_value)
        if model is None:
            return None
        return self._model_to_entity(model)

    async def list_by_node_execution_id(
        self, node_execution_id: NodeExecutionId
    ) -> list[NodeExecutionState]:
        query = select(NodeExecutionStateModel).where(
            NodeExecutionStateModel.node_execution_id == node_execution_id.value
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [self._model_to_entity(r) for r in rows if r]

    async def list_by_node_execution_and_direction(
        self, node_execution_id: NodeExecutionId, direction: StateDirection
    ) -> list[NodeExecutionState]:
        query = select(NodeExecutionStateModel).where(
            NodeExecutionStateModel.node_execution_id == node_execution_id.value,
            NodeExecutionStateModel.direction == direction.value,
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [self._model_to_entity(r) for r in rows if r]

    async def save(self, state: NodeExecutionState) -> None:
        model = await self._session.get(NodeExecutionStateModel, state.id.value)
        if model is None:
            model = NodeExecutionStateModel(
                id=state.id.value,
                node_execution_id=state.node_execution_id.value,
                direction=state.direction.value,
                state_data=state.state_data.to_dict(),
                created_at=state.created_at.value,
            )
            self._session.add(model)
        else:
            model.state_data = state.state_data.to_dict()

    async def delete(self, id_: object, now: datetime | None = None) -> None:
        if now is None:
            now = datetime.now(tz=UTC)
        id_value = id_.value if hasattr(id_, "value") else id_
        model = await self._session.get(NodeExecutionStateModel, id_value)
        if model is not None:
            model.deleted_at = now

    async def exists(self, id_: object) -> ExistsResult:
        id_value = id_.value if hasattr(id_, "value") else id_
        model = await self._session.get(NodeExecutionStateModel, id_value)
        return ExistsResult(model is not None)

    @staticmethod
    def _model_to_entity(model: NodeExecutionStateModel) -> NodeExecutionState:
        return NodeExecutionState(
            id=NodeExecutionStateId(model.id),
            node_execution_id=NodeExecutionId(model.node_execution_id),
            direction=StateDirection(model.direction),
            state_data=StateData(dict(model.state_data or {})),
            created_at=CreatedAt.from_datetime(model.created_at),
        )
