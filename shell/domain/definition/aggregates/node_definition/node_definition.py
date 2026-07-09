from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.aggregates.node_definition.events.node_definition_created_event import (
    NodeDefinitionCreatedEvent,
)
from shell.domain.definition.aggregates.node_definition.value_objects.max_step import MaxStep
from shell.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
    NodeDefinitionId,
)
from shell.domain.definition.aggregates.node_definition.value_objects.node_role_name import (
    NodeRoleName,
)
from shell.domain.definition.aggregates.node_definition.value_objects.node_type_name import (
    NodeTypeName,
)
from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.platform.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.platform.value_objects.mode import Mode


class NodeDefinition(AggregateRoot[NodeDefinitionId]):
    __slots__ = (
        "_mode",
        "_role",
        "_node_type",
        "_max_step",
    )

    def __init__(
        self,
        id: NodeDefinitionId,
        mode: Mode,
        role: NodeRoleName,
        node_type: NodeTypeName,
        max_step: MaxStep | None = None,
    ) -> None:
        super().__init__(id)
        self._mode = mode
        self._role = role if isinstance(role, NodeRoleName) else NodeRoleName(role)
        self._node_type = (
            node_type if isinstance(node_type, NodeTypeName) else NodeTypeName(node_type)
        )
        self._max_step = (
            max_step if max_step is None or isinstance(max_step, MaxStep) else MaxStep(max_step)
        )

    @classmethod
    def restore(
        cls,
        id: NodeDefinitionId,
        mode: Mode,
        role: NodeRoleName,
        node_type: NodeTypeName,
        max_step: MaxStep | None = None,
    ) -> NodeDefinition:
        return cls(
            id=id,
            mode=mode,
            role=role,
            node_type=node_type,
            max_step=max_step,
        )

    @classmethod
    def create(
        cls,
        id: NodeDefinitionId,
        mode: Mode,
        role: NodeRoleName,
        node_type: NodeTypeName,
        max_step: MaxStep | None = None,
        now: datetime | None = None,
    ) -> NodeDefinition:
        instance = cls(
            id=id,
            mode=mode,
            role=role,
            node_type=node_type,
            max_step=max_step,
        )

        if now is not None:
            instance.append_event(
                NodeDefinitionCreatedEvent.now(
                    node_definition_id=id,
                    role=role,
                    node_type=node_type,
                    now=CreatedAt.from_datetime(now),
                )
            )

        return instance

    @property
    def mode(self) -> Mode:
        return self._mode

    @property
    def role(self) -> NodeRoleName:
        return self._role

    @property
    def node_type(self) -> NodeTypeName:
        return self._node_type

    @property
    def max_step(self) -> MaxStep | None:
        return self._max_step
