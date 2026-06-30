from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.execution.aggregates.graph_execution_state.graph_execution_state import (
    GraphExecutionState,
)
from shell.domain.execution.aggregates.graph_execution_state.repositories.graph_execution_state_repository import (
    GraphExecutionStateRepository,
)
from shell.domain.execution.aggregates.graph_execution_state.value_objects.graph_execution_state_id import (
    GraphExecutionStateId,
)
from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
    GraphNodeExecution,
)
from shell.domain.execution.aggregates.graph_node_execution.repositories.graph_node_execution_repository import (
    GraphNodeExecutionRepository,
)
from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.execution.value_objects.graph_definition_id import GraphDefinitionIdRef
from shell.domain.execution.value_objects.graph_node_definition_id import GraphNodeDefinitionId
from shell.domain.execution.value_objects.node_order import NodeOrder
from shell.domain.execution.value_objects.node_role import NodeRole
from shell.domain.execution.value_objects.node_type import NodeType
from shell.domain.execution.value_objects.remaining_retries import RemainingRetries
from shell.domain.execution.value_objects.retry_delay_seconds import RetryDelaySeconds
from shell.domain.execution.value_objects.timeout_seconds import TimeoutSeconds
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.mode import Mode
from shell.domain.platform.value_objects.state_direction import StateDirection

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.aggregates.graph_execution.events.graph_execution_sub_graph_spawn_requested_event import (
        GraphExecutionSubGraphSpawnRequestedEvent,
    )
    from shell.domain.execution.aggregates.graph_execution.ports.graph_execution_definition_provider import (
        GraphExecutionDefinitionProvider,
    )
    from shell.domain.execution.ports.sub_graph_governance import SubGraphGovernance
    from shell.domain.execution.ports.sub_graph_security import SubGraphSecurity
    from shell.domain.execution.ports.sub_graph_versioning import SubGraphVersioning
    from shell.domain.platform.ports.log import Logger
    from shell.domain.platform.ports.time import Clock


class SubGraphSpawnRequestedHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        id_generator: IdGenerator,
        logger: Logger,
        definition_provider: GraphExecutionDefinitionProvider,
        governance: SubGraphGovernance | None = None,
        security: SubGraphSecurity | None = None,
        versioning: SubGraphVersioning | None = None,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator
        self._logger = logger
        self._definition_provider = definition_provider
        self._governance = governance
        self._security = security
        self._versioning = versioning

    async def handle(self, event: GraphExecutionSubGraphSpawnRequestedEvent) -> None:
        async with self._unit_of_work as unit_of_work:
            parent = await unit_of_work.repository(GraphExecutionRepository).get_by_id(
                event.parent_graph_execution_id
            )
            if parent is None:
                self._logger.warning(
                    "sub_graph_spawn.parent_not_found",
                    parent_id=event.parent_graph_execution_id.value,
                )
                return

            now = self._clock.now()

            if self._governance is not None:
                allowed = await self._governance.can_spawn(
                    parent.id,
                    event.graph_definition_id.value,
                    parent.depth.value + 1,
                )
                if not allowed:
                    self._logger.warning(
                        "sub_graph_spawn.governance_rejected",
                        parent_id=parent.id.value,
                        definition_id=event.graph_definition_id,
                    )
                    return

            if self._versioning is not None:
                graph_definition = await self._versioning.resolve_definition(
                    event.graph_definition_id.value, None, parent.id
                )
                if graph_definition is None:
                    self._logger.warning(
                        "sub_graph_spawn.definition_not_found",
                        definition_id=event.graph_definition_id,
                    )
                    return
            else:
                resolved = await self._definition_provider.get_graph_definition(
                    event.graph_definition_id.value
                )
                if resolved is None:
                    self._logger.warning(
                        "sub_graph_spawn.definition_not_found",
                        definition_id=event.graph_definition_id,
                    )
                    return
                graph_definition = resolved

            state_input: dict[str, Any] = event.state_input.to_dict()
            if self._security is not None:
                scope = await self._security.resolve_scope(
                    parent.id, event.graph_definition_id.value
                )
                state_input = await self._security.filter_state(state_input, scope)

            child_id = event.child_graph_execution_id
            child = GraphExecution.create_sub_graph(
                id_=child_id,
                task_execution_id=parent.task_execution_id,
                parent_id=parent.id,
                parent_depth=parent.depth,
                max_subgraph_depth=parent.max_subgraph_depth,
            )

            node_defs = graph_definition.graph_node_execution_definitions
            node_definition_ids = [GraphNodeDefinitionId.generate() for _ in node_defs]
            child.prepare_node_definitions(
                graph_definition_id=GraphDefinitionIdRef(graph_definition.id),
                graph_node_definition_ids=node_definition_ids,
            )

            for i, node_def in enumerate(node_defs):
                node_id = GraphNodeExecutionId.generate()
                node = GraphNodeExecution(
                    id=node_id,
                    graph_execution_id=child_id,
                    node_definition_id=node_definition_ids[i],
                    role=NodeRole(node_def.role),
                    position=NodeOrder(node_def.position),
                    mode=Mode(node_def.mode),
                    node_type=NodeType(node_def.node_type),
                    remaining_retries=RemainingRetries(node_def.retries),
                    retry_delay_seconds=RetryDelaySeconds(0),
                    timeout_seconds=TimeoutSeconds(node_def.timeout),
                )
                await unit_of_work.repository(GraphNodeExecutionRepository).save(node)
                child.attach_node_execution(
                    node_definition_id=node_definition_ids[i],
                    node_execution_id=node_id,
                    now=now,
                )

            if state_input:
                state = GraphExecutionState.create(
                    id_=GraphExecutionStateId.generate(),
                    graph_execution_id=child.id,
                    direction=StateDirection.IN,
                    now=CreatedAt.from_datetime(now),
                )
                state.patch(state_input)
                await unit_of_work.repository(GraphExecutionStateRepository).save(state)
                unit_of_work.stage_events(state.pull_events())

            await unit_of_work.repository(GraphExecutionRepository).save(child)
            unit_of_work.stage_events(child.pull_events())

            self._logger.info(
                "sub_graph_spawn.completed",
                parent_id=parent.id.value,
                child_id=child_id.value,
                node_count=len(node_defs),
                definition_id=event.graph_definition_id,
            )
