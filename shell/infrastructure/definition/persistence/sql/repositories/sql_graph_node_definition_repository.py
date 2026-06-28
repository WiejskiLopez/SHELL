from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.aggregates.graph_node_definition.repositories import (
    GraphNodeDefinitionRepository,
)
from shell.infrastructure.definition.persistence.sql.models import (
    GraphNodeDefinitionModel,
)
from sqlalchemy import select

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.definition.aggregates.graph_node_definition.graph_node_definition import (
        GraphNodeDefinition,
    )
    from shell.domain.definition.aggregates.graph_node_definition.value_objects.graph_node_definition_id import (
        GraphNodeDefinitionId,
    )
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlGraphNodeDefinitionRepository(GraphNodeDefinitionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, graph_node_definition_id: GraphNodeDefinitionId,
    ) -> GraphNodeDefinition | None:
        from shell.domain.definition.aggregates.graph_node_definition.graph_node_definition import (
            GraphNodeDefinition,
        )

        model = await self._session.get(GraphNodeDefinitionModel, graph_node_definition_id.value)
        if model is None:
            return None
        return self._model_to_entity(model)

    async def list_by_graph_definition_id(
        self, graph_definition_id: GraphDefinitionId,
    ) -> list[GraphNodeDefinition]:
        from shell.domain.definition.aggregates.graph_node_definition.graph_node_definition import (
            GraphNodeDefinition,
        )

        stmt = select(GraphNodeDefinitionModel).where(
            GraphNodeDefinitionModel.graph_definition_id == graph_definition_id.value,
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def save(self, graph_node_definition: GraphNodeDefinition) -> None:
        model = await self._session.get(
            GraphNodeDefinitionModel, graph_node_definition.id.value,
        )
        if model is None:
            model = self._entity_to_model(graph_node_definition)
            self._session.add(model)
        else:
            self._update_model(model, graph_node_definition)

    async def delete(self, id: GraphNodeDefinitionId) -> None:
        model = await self._session.get(GraphNodeDefinitionModel, id.value)
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id: GraphNodeDefinitionId) -> bool:
        model = await self._session.get(GraphNodeDefinitionModel, id.value)
        return model is not None

    def _model_to_entity(
        self, model: GraphNodeDefinitionModel,
    ) -> GraphNodeDefinition:
        from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
            GraphDefinitionId,
        )
        from shell.domain.definition.aggregates.graph_node_definition.graph_node_definition import (
            GraphNodeDefinition,
        )
        from shell.domain.definition.aggregates.graph_node_definition.value_objects.graph_node_definition_id import (
            GraphNodeDefinitionId,
        )
        from shell.domain.definition.value_objects.autopilot import Autopilot
        from shell.domain.definition.value_objects.command_text import CommandText
        from shell.domain.definition.value_objects.initial_status import InitialStatus
        from shell.domain.definition.value_objects.log_level import LogLevel
        from shell.domain.definition.value_objects.max_step import MaxStep
        from shell.domain.definition.value_objects.model_name import ModelName
        from shell.domain.definition.value_objects.no_ask_user import NoAskUser
        from shell.domain.definition.value_objects.node_position import NodePosition
        from shell.domain.definition.value_objects.node_role_name import NodeRoleName
        from shell.domain.definition.value_objects.node_type_name import NodeTypeName
        from shell.domain.definition.value_objects.retry_count import RetryCount
        from shell.domain.definition.value_objects.script_text import ScriptText
        from shell.domain.definition.value_objects.script_type_name import ScriptTypeName
        from shell.domain.definition.value_objects.transition_timeout_seconds import (
            TransitionTimeoutSeconds,
        )
        from shell.domain.platform.value_objects.mode import Mode

        return GraphNodeDefinition(
            id=GraphNodeDefinitionId(model.id),
            graph_definition_id=GraphDefinitionId(model.graph_definition_id),
            position=NodePosition(model.position),
            mode=Mode(model.mode),
            role=NodeRoleName(model.role),
            node_type=NodeTypeName(model.node_type),
            model=ModelName(model.model) if model.model else None,
            command=CommandText(model.command) if model.command else None,
            timeout=TransitionTimeoutSeconds(model.timeout) if model.timeout is not None else None,
            retries=RetryCount(model.retries) if model.retries is not None else None,
            log_level=LogLevel(model.log_level) if model.log_level else None,
            max_step=MaxStep(model.max_step) if model.max_step is not None else None,
            no_ask_user=NoAskUser(model.no_ask_user) if model.no_ask_user is not None else None,
            autopilot=Autopilot(model.autopilot) if model.autopilot is not None else None,
            status_initial=InitialStatus(model.status_initial) if model.status_initial else None,
            script=ScriptText(model.script) if model.script else None,
            script_type=ScriptTypeName(model.script_type) if model.script_type else None,
        )

    def _entity_to_model(self, entity: GraphNodeDefinition) -> GraphNodeDefinitionModel:
        return GraphNodeDefinitionModel(
            id=entity.id.value,
            graph_definition_id=entity.graph_definition_id.value,
            position=entity.position.value,
            mode=entity.mode.value,
            role=entity.role.value,
            node_type=entity.node_type.value,
            model=entity.model.value if entity.model else None,
            command=entity.command.value if entity.command else None,
            timeout=entity.timeout.value if entity.timeout is not None else None,
            retries=entity.retries.value if entity.retries is not None else None,
            log_level=entity.log_level.value if entity.log_level else None,
            max_step=entity.max_step.value if entity.max_step is not None else None,
            no_ask_user=entity.no_ask_user.value if entity.no_ask_user is not None else None,
            autopilot=entity.autopilot.value if entity.autopilot is not None else None,
            status_initial=entity.status_initial.value if entity.status_initial else None,
            script=entity.script.value if entity.script else None,
            script_type=entity.script_type.value if entity.script_type else None,
        )

    def _update_model(self, model: GraphNodeDefinitionModel, entity: GraphNodeDefinition) -> None:
        model.position = entity.position.value
        model.mode = entity.mode.value
        model.role = entity.role.value
        model.node_type = entity.node_type.value
        model.model = entity.model.value if entity.model else None
        model.command = entity.command.value if entity.command else None
        model.timeout = entity.timeout.value if entity.timeout is not None else None
        model.retries = entity.retries.value if entity.retries is not None else None
        model.log_level = entity.log_level.value if entity.log_level else None
        model.max_step = entity.max_step.value if entity.max_step is not None else None
        model.no_ask_user = entity.no_ask_user.value if entity.no_ask_user is not None else None
        model.autopilot = entity.autopilot.value if entity.autopilot is not None else None
        model.status_initial = entity.status_initial.value if entity.status_initial else None
        model.script = entity.script.value if entity.script else None
        model.script_type = entity.script_type.value if entity.script_type else None
