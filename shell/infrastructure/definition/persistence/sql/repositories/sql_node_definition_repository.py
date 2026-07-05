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
                NodeLinkDefinitionModel.node_definition_id
                == NodeDefinitionModel.id,
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
            position=NodePosition(model.position),
            mode=Mode(model.mode),
            role=NodeRoleName(model.role),
            node_type=NodeTypeName(model.node_type),
            model=ModelName(model.model) if model.model else None,
            command=CommandText(model.command) if model.command else None,
            timeout=model.timeout if model.timeout is not None else None,
            retries=RetryCount(model.retries) if model.retries is not None else None,
            log_level=LogLevel(model.log_level) if model.log_level else None,
            max_step=MaxStep(model.max_step) if model.max_step is not None else None,
            no_ask_user=NoAskUser(model.no_ask_user) if model.no_ask_user is not None else None,
            autopilot=Autopilot(model.autopilot) if model.autopilot is not None else None,
            status_initial=InitialStatus(model.status_initial) if model.status_initial else None,
            script=ScriptText(model.script) if model.script else None,
            script_type=ScriptTypeName(model.script_type) if model.script_type else None,
        )

    def _entity_to_model(self, entity: NodeDefinition) -> NodeDefinitionModel:
        return NodeDefinitionModel(
            id=entity.id.value,
            position=entity.position.value,
            mode=entity.mode.value,
            role=entity.role.value,
            node_type=entity.node_type.value,
            model=entity.model.value if entity.model else None,
            command=entity.command.value if entity.command else None,
            timeout=entity.timeout,
            retries=entity.retries.value if entity.retries is not None else None,
            log_level=entity.log_level.value if entity.log_level else None,
            max_step=entity.max_step.value if entity.max_step is not None else None,
            no_ask_user=entity.no_ask_user.value if entity.no_ask_user is not None else None,
            autopilot=entity.autopilot.value if entity.autopilot is not None else None,
            status_initial=entity.status_initial.value if entity.status_initial else None,
            script=entity.script.value if entity.script else None,
            script_type=entity.script_type.value if entity.script_type else None,
        )

    def _update_model(self, model: NodeDefinitionModel, entity: NodeDefinition) -> None:
        model.position = entity.position.value
        model.mode = entity.mode.value
        model.role = entity.role.value
        model.node_type = entity.node_type.value
        model.model = entity.model.value if entity.model else None
        model.command = entity.command.value if entity.command else ""
        model.timeout = entity.timeout  # type: ignore[assignment]
        model.retries = entity.retries.value if entity.retries is not None else 0
        model.log_level = entity.log_level.value if entity.log_level else "INFO"
        model.max_step = entity.max_step.value if entity.max_step is not None else 0
        model.no_ask_user = entity.no_ask_user.value if entity.no_ask_user is not None else False
        model.autopilot = entity.autopilot.value if entity.autopilot is not None else False
        model.status_initial = entity.status_initial.value if entity.status_initial else ""
        model.script = entity.script.value if entity.script else ""
        model.script_type = entity.script_type.value if entity.script_type else ""
