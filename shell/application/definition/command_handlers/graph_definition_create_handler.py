from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.aggregates.graph_definition.graph_definition import GraphDefinition
from shell.domain.definition.aggregates.graph_node_definition.graph_node_definition import (
    GraphNodeDefinition,
)
from shell.domain.definition.aggregates.graph_node_link_definition.graph_node_link_definition import (
    GraphNodeLinkDefinition,
)
from shell.domain.definition.aggregates.graph_node_link_definition.repositories.graph_node_link_definition_repository import (
    GraphNodeLinkDefinitionRepository,
)
from shell.domain.definition.aggregates.graph_node_link_definition.value_objects.graph_node_link_definition_id import (
    GraphNodeLinkDefinitionId,
)
from shell.domain.definition.repositories.graph_definition_repository.graph_definition_repository import (
    GraphDefinitionRepository,
)
from shell.domain.definition.repositories.graph_definition_repository.graph_node_definition_repository import (
    GraphNodeDefinitionRepository,
)
from shell.domain.definition.value_objects.graph_name import GraphName
from shell.domain.definition.value_objects.ids import GraphDefinitionId, GraphNodeDefinitionId
from shell.domain.definition.value_objects.node_position import NodePosition
from shell.domain.definition.value_objects.node_role_name import NodeRoleName
from shell.domain.definition.value_objects.node_type_name import NodeTypeName
from shell.domain.definition.value_objects.purpose import Purpose
from shell.domain.platform.value_objects.mode import Mode

if TYPE_CHECKING:
    from shell.application.definition.commands.create_graph_definition_command import (
        CreateGraphDefinitionCommand,
    )
    from shell.application.platform.ports.identity import IdGenerator
    from shell.application.platform.ports.unit_of_work import UnitOfWork
    from shell.domain.platform.ports.time import Clock


class GraphDefinitionCreateHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator

    async def handle(self, command: CreateGraphDefinitionCommand) -> str:
        now = self._clock.now()
        graph_id = self._id_generator.new_id(GraphDefinitionId)
        node_ids: list[GraphNodeDefinitionId] = []
        node_aggregates: list[GraphNodeDefinition] = []

        for node_dict in command.graph_node_definitions:
            node_id = self._id_generator.new_id(GraphNodeDefinitionId)
            node_ids.append(node_id)

            node = GraphNodeDefinition.create(
                id=node_id,
                position=NodePosition(node_dict.get("position", 0)),
                mode=Mode(node_dict.get("mode", "worker")),
                role=NodeRoleName(node_dict.get("role", "")),
                node_type=NodeTypeName(node_dict.get("node_type", "")),
                now=now,
            )
            node_aggregates.append(node)

        async with self._unit_of_work as unit_of_work:
            for node in node_aggregates:
                await unit_of_work.repository(GraphNodeDefinitionRepository).save(node)
                unit_of_work.stage_events(node.pull_events())

            graph = GraphDefinition.create(
                id=graph_id,
                name=GraphName(command.name),
                purpose=Purpose(command.purpose),
                now=now,
            )
            await unit_of_work.repository(GraphDefinitionRepository).save(graph)
            unit_of_work.stage_events(graph.pull_events())

            for node_id in node_ids:
                link = GraphNodeLinkDefinition(
                    id=GraphNodeLinkDefinitionId.generate(),
                    graph_definition_id=graph_id,
                    graph_node_definition_id=node_id,
                )
                await unit_of_work.repository(
                    GraphNodeLinkDefinitionRepository
                ).save(link)

        return graph_id.value
