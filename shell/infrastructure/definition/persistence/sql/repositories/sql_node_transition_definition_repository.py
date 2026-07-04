from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.definition.aggregates.node_transition_definition.repositories import (
    NodeTransitionDefinitionRepository,
)
from shell.infrastructure.definition.persistence.sql.models import (
    NodeTransitionDefinitionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.definition.aggregates.node_transition_definition.node_transition_definition import (
        NodeTransitionDefinition,
    )
    from shell.domain.definition.aggregates.node_transition_definition.value_objects.node_transition_definition_id import (
        NodeTransitionDefinitionId,
    )
    from shell.domain.platform.value_objects.exists_result import ExistsResult


from shell.domain.definition.value_objects.transition_timeout_seconds import (
            TransitionTimeoutSeconds,
        )
from shell.domain.definition.value_objects.transition_retry_delay import (
            TransitionRetryDelay,
        )
from shell.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
            NodeDefinitionId,
        )
class SqlNodeTransitionDefinitionRepository(NodeTransitionDefinitionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self,
        id: NodeTransitionDefinitionId,
    ) -> NodeTransitionDefinition | None:

        model = await self._session.get(NodeTransitionDefinitionModel, id.value)
        if model is None:
            return None
        return self._model_to_entity(model)

    async def list_by_graph_definition_id(
        self,
        graph_definition_id: GraphDefinitionId,
    ) -> list[NodeTransitionDefinition]:

        stmt = select(NodeTransitionDefinitionModel).where(
            NodeTransitionDefinitionModel.graph_definition_id == graph_definition_id.value,
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def save(
        self,
        transition: NodeTransitionDefinition,
    ) -> None:
        model = await self._session.get(
            NodeTransitionDefinitionModel,
            transition.id.value,
        )
        if model is None:
            model = self._entity_to_model(transition)
            self._session.add(model)

    async def delete(self, id: NodeTransitionDefinitionId) -> None:
        model = await self._session.get(NodeTransitionDefinitionModel, id.value)
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id: NodeTransitionDefinitionId) -> ExistsResult:
        model = await self._session.get(NodeTransitionDefinitionModel, id.value)
        return ExistsResult(model is not None)

    def _model_to_entity(
        self,
        model: NodeTransitionDefinitionModel,
    ) -> NodeTransitionDefinition:
        source_id = model.source_node_definition_id
        return NodeTransitionDefinition(
            id=NodeTransitionDefinitionId(model.id),
            graph_definition_id=GraphDefinitionId(model.graph_definition_id),
            source_node_definition_id=NodeDefinitionId(source_id) if source_id else None,
            target_node_definition_id=NodeDefinitionId(model.target_node_definition_id),
            transition_type=EdgeType(model.transition_type),
            priority=TransitionPriority(model.priority) if model.priority is not None else None,
            condition_expression=ConditionExpression(model.condition_expression)
            if model.condition_expression
            else None,
            condition_language=ConditionLanguage(model.condition_language)
            if model.condition_language
            else None,
            max_loop_count=MaxLoopCount(model.max_loop_count)
            if model.max_loop_count is not None
            else None,
            timeout_seconds=TransitionTimeoutSeconds(model.timeout_seconds)
            if model.timeout_seconds is not None
            else None,
            retry_count=RetryCount(model.retry_count) if model.retry_count is not None else None,
            retry_delay_seconds=TransitionRetryDelay(model.retry_delay_seconds)
            if model.retry_delay_seconds is not None
            else None,
            data_mapping=DataMapping(model.data_mapping)
            if model.data_mapping is not None
            else None,
            label=TransitionLabel(model.label) if model.label else None,
        )

    def _entity_to_model(
        self,
        entity: NodeTransitionDefinition,
    ) -> NodeTransitionDefinitionModel:

        return NodeTransitionDefinitionModel(
            id=entity.id.value,
            graph_definition_id=entity.graph_definition_id.value,
            source_node_definition_id=entity.source_node_definition_id.value
            if entity.source_node_definition_id
            else None,
            target_node_definition_id=entity.target_node_definition_id.value,
            transition_type=entity.transition_type.value,
            priority=entity.priority.value if entity.priority else None,
            condition_expression=entity.condition_expression.value
            if entity.condition_expression
            else None,
            condition_language=entity.condition_language.value
            if entity.condition_language
            else None,
            max_loop_count=entity.max_loop_count.value
            if entity.max_loop_count is not None
            else None,
            timeout_seconds=entity.timeout_seconds.value
            if entity.timeout_seconds is not None
            else None,
            retry_count=entity.retry_count.value if entity.retry_count is not None else None,
            retry_delay_seconds=entity.retry_delay_seconds.value
            if entity.retry_delay_seconds is not None
            else None,
            data_mapping=entity.data_mapping.value if entity.data_mapping else None,
            label=entity.label.value if entity.label else None,
        )
