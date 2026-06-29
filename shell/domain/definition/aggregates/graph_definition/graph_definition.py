from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
    GraphDefinitionId,
)
from shell.domain.definition.value_objects.graph_name import GraphName
from shell.domain.definition.value_objects.purpose import Purpose
from shell.domain.definition.value_objects.system_role import SystemRole
from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.platform.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.definition.value_objects.ids import (
        GraphNodeDefinitionId,
        GraphNodeTransitionDefinitionId,
    )


class GraphDefinition(AggregateRoot[GraphDefinitionId]):
    __slots__ = (
        "_name",
        "_purpose",
        "_system_role",
        "_graph_node_definition_ids",
        "_transition_definition_ids",
    )

    def __init__(
        self,
        id: GraphDefinitionId,
        name: GraphName,
        purpose: Purpose,
        system_role: SystemRole | None = None,
        graph_node_definition_ids: list[GraphNodeDefinitionId] | None = None,
        transition_definition_ids: list[GraphNodeTransitionDefinitionId] | None = None,
    ) -> None:
        super().__init__(id)
        self._name = name if isinstance(name, GraphName) else GraphName(name)
        self._purpose = purpose if isinstance(purpose, Purpose) else Purpose(purpose)
        self._system_role = (
            system_role if isinstance(system_role, SystemRole) else SystemRole(system_role) if system_role is not None else None
        )
        self._graph_node_definition_ids = list(graph_node_definition_ids) if graph_node_definition_ids else []
        self._transition_definition_ids = list(transition_definition_ids) if transition_definition_ids else []

    @classmethod
    def restore(
        cls,
        id: GraphDefinitionId,
        name: GraphName,
        purpose: Purpose,
        system_role: SystemRole | None = None,
        graph_node_definition_ids: list[GraphNodeDefinitionId] | None = None,
        transition_definition_ids: list[GraphNodeTransitionDefinitionId] | None = None,
    ) -> GraphDefinition:
        return cls(
            id=id,
            name=name,
            purpose=purpose,
            system_role=system_role,
            graph_node_definition_ids=graph_node_definition_ids,
            transition_definition_ids=transition_definition_ids,
        )

    @classmethod
    def create(
        cls,
        id: GraphDefinitionId,
        name: GraphName,
        purpose: Purpose,
        system_role: SystemRole | None = None,
        graph_node_definition_ids: list[GraphNodeDefinitionId] | None = None,
        transition_definition_ids: list[GraphNodeTransitionDefinitionId] | None = None,
        now: datetime | None = None,
    ) -> GraphDefinition:
        if not name.value.strip():
            raise ValueError("GraphDefinition name cannot be empty")
        if not purpose.value.strip():
            raise ValueError("GraphDefinition purpose cannot be empty")

        instance = cls(
            id=id,
            name=name,
            purpose=purpose,
            system_role=system_role,
            graph_node_definition_ids=graph_node_definition_ids,
            transition_definition_ids=transition_definition_ids,
        )

        from shell.domain.definition.aggregates.graph_definition.events.graph_definition_created_event import (
            GraphDefinitionCreatedEvent,
        )

        if now is not None:
            instance.append_event(
                GraphDefinitionCreatedEvent.now(
                    graph_definition_id=id,
                    name=name,
                    purpose=purpose,
                    now=CreatedAt.from_datetime(now),
                )
            )

        return instance

    @property
    def name(self) -> GraphName:
        return self._name

    @property
    def purpose(self) -> Purpose:
        return self._purpose

    @property
    def system_role(self) -> SystemRole | None:
        return self._system_role

    @property
    def graph_node_definition_ids(self) -> tuple[GraphNodeDefinitionId, ...]:
        return tuple(self._graph_node_definition_ids)

    @property
    def transition_definition_ids(self) -> tuple[GraphNodeTransitionDefinitionId, ...]:
        return tuple(self._transition_definition_ids)
