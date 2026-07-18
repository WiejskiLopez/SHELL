from __future__ import annotations

from typing import TYPE_CHECKING

from definition.aggregates.node_definition.events.nodedefinition_deleted_event import (
    NodeDefinitionDeletedEvent,
)
from definition.aggregates.node_definition.events.nodedefinition_updated_event import (
    NodeDefinitionUpdatedEvent,
)

from shell.domain.definition.aggregates.node_definition.events.node_definition_created_event import (
    NodeDefinitionCreatedEvent,
)
from shell.domain.definition.aggregates.node_definition.value_objects.max_step import MaxStep
from shell.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
    NodeDefinitionId,
)
from shell.domain.definition.aggregates.node_definition.value_objects.node_type import NodeType
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.deleted_at import DeletedAt


class NodeDefinition(AggregateRoot[NodeDefinitionId]):
    __slots__ = (
        "_updated_at",
        "_created_at",
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


    @classmethod
    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            NodeDefinitionUpdatedEvent.now(
                nodedefinition_id=self._id,
                now=now,
            )
        )




    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            NodeDefinitionDeletedEvent.now(
                nodedefinition_id=self._id,
                now=CreatedAt.from_datetime(now.value),
            )
        )
    @property
    def node_type(self) -> NodeType:
        return self._node_type

    @property
    def max_step(self) -> MaxStep | None:
        return self._max_step

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
    def _new(
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


    @classmethod
    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            NodeDefinitionUpdatedEvent.now(
                nodedefinition_id=self._id,
                now=now,
            )
        )




    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            NodeDefinitionDeletedEvent.now(
                nodedefinition_id=self._id,
                now=CreatedAt.from_datetime(now.value),
            )
        )
    @property
    def node_type(self) -> NodeType:
        return self._node_type

    @property
    def max_step(self) -> MaxStep | None:
        return self._max_step
