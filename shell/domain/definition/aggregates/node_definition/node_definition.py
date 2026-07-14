from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.aggregates.node_definition.events.node_definition_created_event import (
    NodeDefinitionCreatedEvent,
)
from shell.domain.definition.aggregates.node_definition.value_objects.max_step import MaxStep
from shell.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
    NodeDefinitionId,
)
from shell.domain.definition.aggregates.node_definition.value_objects.node_type import NodeType
from shell.platform.domain.base.aggregate_root import AggregateRoot

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.created_at import CreatedAt


class NodeDefinition(AggregateRoot[NodeDefinitionId]):
    __slots__ = (
        "_node_type",
        "_max_step",
    )

    def __init__(
        self,
        id: NodeDefinitionId,
        node_type: NodeType,
        max_step: MaxStep | None = None,
    ) -> None:
        super().__init__(id)
        self._node_type = node_type if isinstance(node_type, NodeType) else NodeType(node_type)
        self._max_step = (
            max_step if max_step is None or isinstance(max_step, MaxStep) else MaxStep(max_step)
        )

    @classmethod
    def restore(
        cls,
        id: NodeDefinitionId,
        node_type: NodeType,
        max_step: MaxStep | None = None,
    ) -> NodeDefinition:
        return cls(
            id=id,
            node_type=node_type,
            max_step=max_step,
        )

    @classmethod
    def create(
        cls,
        id: NodeDefinitionId,
        node_type: NodeType,
        max_step: MaxStep | None = None,
        now: CreatedAt | None = None,
    ) -> NodeDefinition:
        instance = cls(
            id=id,
            node_type=node_type,
            max_step=max_step,
        )

        if now is not None:
            instance.append_event(
                NodeDefinitionCreatedEvent.now(
                    node_definition_id=id,
                    now=now,
                )
            )

        return instance

    @property
    def node_type(self) -> NodeType:
        return self._node_type

    @property
    def max_step(self) -> MaxStep | None:
        return self._max_step
