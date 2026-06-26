from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.graph_execution.events.graph_execution_sub_graph_spawn_requested_event import (
    GraphExecutionSubGraphSpawnRequestedEvent,
)
from shell.domain.execution.aggregates.graph_execution_state.graph_execution_state import (
    GraphExecutionState,
)
from shell.domain.execution.aggregates.graph_execution_state.value_objects.graph_execution_state_id import (
    GraphExecutionStateId,
)
from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
    GraphNodeExecution,
)
from shell.domain.execution.value_objects.node_role import NodeRole
from shell.domain.execution.value_objects.state_kind import StateKind
from shell.domain.platform.value_objects.mode import Mode

if TYPE_CHECKING:
    from shell.application.platform.ports.identity import IdGenerator
    from shell.domain.platform.ports.log import Logger
    from shell.domain.platform.ports.time import Clock
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.execution.ports.graph_execution_definition_provider import (
        GraphExecutionDefinitionProvider,
    )
    from shell.domain.execution.ports.sub_graph_governance import SubGraphGovernance
    from shell.domain.execution.ports.sub_graph_security import SubGraphSecurity
    from shell.domain.execution.ports.sub_graph_versioning import SubGraphVersioning


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
            parent = await unit_of_work.graph_execution_repository.get_by_id(event.parent_graph_execution_id)
            if parent is None:
                self._logger.warning(
                    "sub_graph_spawn.parent_not_found",
                    parent_id=event.parent_graph_execution_id.value,
                )
                return

            now = self._clock.now()

            if self._governance is not None:
                allowed = await self._governance.can_spawn(
                    parent.id.value,
                    event.graph_definition_id,
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
                    event.graph_definition_id, None, parent.id.value
                )
            else:
                graph_definition = await self._definition_provider.get_graph_definition(event.graph_definition_id)
                if graph_definition is None:
                    self._logger.warning(
                        "sub_graph_spawn.definition_not_found",
                        definition_id=event.graph_definition_id,
                    )
                    return

            state_input: dict[str, Any] = dict(event.state_input) if event.state_input else {}
            if self._security is not None:
                scope = await self._security.resolve_scope(parent.id.value, event.graph_definition_id)
                state_input = await self._security.filter_state(state_input, scope)

            child_id = event.child_graph_execution_id
            child = GraphExecution.create_sub_graph(
                id_=child_id,
                task_execution_id=parent.task_execution_id,
                parent_id=parent.id,
                parent_depth=parent.depth.value,
            )
            if state_input:
                state = GraphExecutionState.create(
                    id_=GraphExecutionStateId.generate(),
                    graph_execution_id=child.id,
                    kind=StateKind.INPUT,
                    now=now,
                )
                state.patch(state_input)
                await unit_of_work.graph_execution_state_repository.save(state)
                unit_of_work.stage_events(state.pull_events())

            node_defs = graph_definition.graph_node_execution_definitions
            for node_def in node_defs:
                node_id = self._id_generator.new_graph_node_execution_id()
                node = GraphNodeExecution.new(
                    id=node_id,
                    graph_execution_id=child_id,
                    parent_graph_execution_id=event.parent_graph_execution_id,
                    role=NodeRole(node_def.role),
                    position=getattr(node_def, 'position', 0),
                    mode=Mode(getattr(node_def, 'mode', 'worker')),
                    node_type=getattr(node_def, 'node_type', ''),
                    model=getattr(node_def, 'model', ''),
                    command=getattr(node_def, 'command', ''),
                    timeout_seconds=getattr(node_def, 'timeout', 0),
                    max_retries=getattr(node_def, 'retries', 0),
                    log_level=getattr(node_def, 'log_level', 'INFO'),
                    max_step=getattr(node_def, 'max_step', 0) or 0,
                    no_ask_user=getattr(node_def, 'no_ask_user', False),
                    autopilot=getattr(node_def, 'autopilot', False),
                    status_initial=getattr(node_def, 'status_initial', ''),
                    now=now,
                )
                await unit_of_work.graph_node_execution_repository.save(node)
                unit_of_work.stage_events(list(node.pull_events()))

            await unit_of_work.graph_execution_repository.save(child)
            unit_of_work.stage_events(list(child.pull_events()))

            self._logger.info(
                "sub_graph_spawn.completed",
                parent_id=parent.id.value,
                child_id=child_id.value,
                node_count=len(node_defs),
                definition_id=event.graph_definition_id,
            )
