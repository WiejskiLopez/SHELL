from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.definition.aggregates.node_definition.repositories import (
    NodeDefinitionRepository,
)
from shell.domain.platform.value_objects.exists_result import ExistsResult
from shell.infrastructure.definition.persistence.sql.models import (
    NodeDefinitionModel,
    NodeLinkDefinitionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )


from shell.domain.definition.aggregates.node_definition.node_definition import (
    NodeDefinition,
)
from shell.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
    NodeDefinitionId,
)
from shell.domain.definition.value_objects.max_step import MaxStep
from shell.domain.definition.value_objects.node_role_name import NodeRoleName
from shell.domain.definition.value_objects.node_type_name import NodeTypeName
from shell.domain.platform.value_objects.mode import Mode


class SqlNodeDefinitionRepository(NodeDefinitionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self,
        node_definition_id: NodeDefinitionId,
    ) -> NodeDefinition | None:

        model = await self._session.get(NodeDefinitionModel, node_definition_id.value)
        if model is None:
            return None
        return self._model_to_entity(model)

    async def list_by_graph_definition_id(
        self,
        graph_definition_id: GraphDefinitionId,
    ) -> list[NodeDefinition]:

        stmt = (
            select(NodeDefinitionModel)
            .join(
                NodeLinkDefinitionModel,
                NodeLinkDefinitionModel.node_definition_id == NodeDefinitionModel.id,
            )
            .where(NodeLinkDefinitionModel.graph_definition_id == graph_definition_id.value)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def save(self, node_definition: NodeDefinition) -> None:
        model = await self._session.get(
            NodeDefinitionModel,
            node_definition.id.value,
        )
        if model is None:
            model = self._entity_to_model(node_definition)
            self._session.add(model)
        else:
            self._update_model(model, node_definition)

    async def delete(self, id: NodeDefinitionId, now: datetime | None = None) -> None:
        if now is None:
            now = datetime.now(tz=UTC)
        model = await self._session.get(NodeDefinitionModel, id.value)
        if model is not None:
            model.deleted_at = now

    async def exists(self, id: NodeDefinitionId) -> ExistsResult:
        model = await self._session.get(NodeDefinitionModel, id.value)
        return ExistsResult(model is not None)

    def _model_to_entity(
        self,
        model: NodeDefinitionModel,
    ) -> NodeDefinition:
        return NodeDefinition(
            id=NodeDefinitionId(model.id),
            mode=Mode(model.mode),
            role=NodeRoleName(model.role),
            node_type=NodeTypeName(model.node_type),
            max_step=MaxStep(model.max_step) if model.max_step is not None else None,
        )

    def _entity_to_model(self, entity: NodeDefinition) -> NodeDefinitionModel:
        return NodeDefinitionModel(
            id=entity.id.value,
            mode=entity.mode.value,
            role=entity.role.value,
            node_type=entity.node_type.value,
            max_step=entity.max_step.value if entity.max_step is not None else None,
        )

    def _update_model(self, model: NodeDefinitionModel, entity: NodeDefinition) -> None:
        model.mode = entity.mode.value
        model.role = entity.role.value
        model.node_type = entity.node_type.value
        model.max_step = entity.max_step.value if entity.max_step is not None else None
