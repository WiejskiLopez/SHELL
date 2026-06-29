from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.aggregates.graph_node_transition_definition.repositories import (
    GraphNodeTransitionDefinitionRepository,
)
from shell.infrastructure.definition.persistence.sql.models import (
    GraphNodeTransitionDefinitionModel,
)
from sqlalchemy import select

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.definition.aggregates.graph_node_transition_definition.graph_node_transition_definition import (
        GraphNodeTransitionDefinition,
    )
    from shell.domain.definition.aggregates.graph_node_transition_definition.value_objects.graph_node_transition_definition_id import (
        GraphNodeTransitionDefinitionId,
    )
    from shell.domain.platform.value_objects.exists_result import ExistsResult
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlGraphNodeTransitionDefinitionRepository(GraphNodeTransitionDefinitionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, id: GraphNodeTransitionDefinitionId,
    ) -> GraphNodeTransitionDefinition | None:
        from shell.domain.definition.aggregates.graph_node_transition_definition.graph_node_transition_definition import (
            GraphNodeTransitionDefinition,
        )

        model = await self._session.get(GraphNodeTransitionDefinitionModel, id.value)
        if model is None:
            return None
        return self._model_to_entity(model)

    async def list_by_graph_definition_id(
        self, graph_definition_id: GraphDefinitionId,
    ) -> list[GraphNodeTransitionDefinition]:
        from shell.domain.definition.aggregates.graph_node_transition_definition.graph_node_transition_definition import (
            GraphNodeTransitionDefinition,
        )

        stmt = select(GraphNodeTransitionDefinitionModel).where(
            GraphNodeTransitionDefinitionModel.graph_definition_id == graph_definition_id.value,
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def save(
        self, transition: GraphNodeTransitionDefinition,
    ) -> None:
        model = await self._session.get(
            GraphNodeTransitionDefinitionModel, transition.id.value,
        )
        if model is None:
            model = self._entity_to_model(transition)
            self._session.add(model)

    async def delete(self, id: GraphNodeTransitionDefinitionId) -> None:
        model = await self._session.get(GraphNodeTransitionDefinitionModel, id.value)
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id: GraphNodeTransitionDefinitionId) -> ExistsResult:
        from shell.domain.platform.value_objects.exists_result import ExistsResult

        model = await self._session.get(GraphNodeTransitionDefinitionModel, id.value)
        return ExistsResult(model is not None)

    def _model_to_entity(
        self, model: GraphNodeTransitionDefinitionModel,
    ) -> GraphNodeTransitionDefinition:
        from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
            GraphDefinitionId,
        )
        from shell.domain.definition.aggregates.graph_node_definition.value_objects.graph_node_definition_id import (
            GraphNodeDefinitionId,
        )
        from shell.domain.definition.aggregates.graph_node_transition_definition.graph_node_transition_definition import (
            GraphNodeTransitionDefinition,
        )
        from shell.domain.definition.aggregates.graph_node_transition_definition.value_objects.graph_node_transition_definition_id import (
            GraphNodeTransitionDefinitionId,
        )
        from shell.domain.definition.value_objects.condition_language import ConditionLanguage
        from shell.domain.definition.value_objects.data_mapping import DataMapping
        from shell.domain.definition.value_objects.max_loop_count import MaxLoopCount
        from shell.domain.definition.value_objects.retry_count import RetryCount
        from shell.domain.definition.value_objects.transition_label import TransitionLabel
        from shell.domain.definition.value_objects.transition_priority import TransitionPriority
        from shell.domain.definition.value_objects.transition_retry_delay import TransitionRetryDelay
        from shell.domain.definition.value_objects.transition_timeout_seconds import (
            TransitionTimeoutSeconds,
        )
        from shell.domain.platform.value_objects.condition_expression import ConditionExpression
        from shell.domain.platform.value_objects.edge_type import EdgeType

        source_id = model.source_node_definition_id
        return GraphNodeTransitionDefinition(
            id=GraphNodeTransitionDefinitionId(model.id),
            graph_definition_id=GraphDefinitionId(model.graph_definition_id),
            source_node_definition_id=GraphNodeDefinitionId(source_id) if source_id else None,
            target_node_definition_id=GraphNodeDefinitionId(model.target_node_definition_id),
            transition_type=EdgeType(model.transition_type),
            priority=TransitionPriority(model.priority) if model.priority is not None else None,
            condition_expression=ConditionExpression(model.condition_expression) if model.condition_expression else None,
            condition_language=ConditionLanguage(model.condition_language) if model.condition_language else None,
            max_loop_count=MaxLoopCount(model.max_loop_count) if model.max_loop_count is not None else None,
            timeout_seconds=TransitionTimeoutSeconds(model.timeout_seconds) if model.timeout_seconds is not None else None,
            retry_count=RetryCount(model.retry_count) if model.retry_count is not None else None,
            retry_delay_seconds=TransitionRetryDelay(model.retry_delay_seconds) if model.retry_delay_seconds is not None else None,
            data_mapping=DataMapping(model.data_mapping) if model.data_mapping is not None else None,
            label=TransitionLabel(model.label) if model.label else None,
        )

    def _entity_to_model(
        self, entity: GraphNodeTransitionDefinition,
    ) -> GraphNodeTransitionDefinitionModel:
        from shell.infrastructure.definition.persistence.sql.mappers.graph_definition_mapper import (
            graph_definition_entity_to_model,
        )

        return GraphNodeTransitionDefinitionModel(
            id=entity.id.value,
            graph_definition_id=entity.graph_definition_id.value,
            source_node_definition_id=entity.source_node_definition_id.value if entity.source_node_definition_id else None,
            target_node_definition_id=entity.target_node_definition_id.value,
            transition_type=entity.transition_type.value,
            priority=entity.priority.value if entity.priority else None,
            condition_expression=entity.condition_expression.value if entity.condition_expression else None,
            condition_language=entity.condition_language.value if entity.condition_language else None,
            max_loop_count=entity.max_loop_count.value if entity.max_loop_count is not None else None,
            timeout_seconds=entity.timeout_seconds.value if entity.timeout_seconds is not None else None,
            retry_count=entity.retry_count.value if entity.retry_count is not None else None,
            retry_delay_seconds=entity.retry_delay_seconds.value if entity.retry_delay_seconds is not None else None,
            data_mapping=entity.data_mapping.value if entity.data_mapping else None,
            label=entity.label.value if entity.label else None,
        )
