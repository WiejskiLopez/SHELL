from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.scheduling.aggregates.scheduler_definition.events.scheduler_definition_created_event import (
    SchedulerDefinitionCreatedEvent,
)
from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_definition_id import (
    SchedulerDefinitionId,
)
from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_description import (
    SchedulerDescription,
)
from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_name import (
    SchedulerName,
)
from shell.platform.domain.base import AggregateRoot
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.enabled import Enabled
if TYPE_CHECKING:
    from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.action_config import (
        ActionConfig,
    )
    from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.execution_policy import (
        ExecutionPolicy,
    )
    from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.trigger_config import (
        TriggerConfig,
    )

class SchedulerDefinition(AggregateRoot[SchedulerDefinitionId]):
    __slots__ = (
        "_name",
        "_description",
        "_trigger_config",
        "_action_config",
        "_execution_policy",
        "_enabled",
        "_created_at",
        "_updated_at",
    )

    def __init__(
        self,
        id: SchedulerDefinitionId,
        name: SchedulerName,
        enabled: Enabled,
        trigger_config: TriggerConfig,
        action_config: ActionConfig,
        execution_policy: ExecutionPolicy,
        created_at: CreatedAt,
        updated_at: Timestamp,
        description: SchedulerDescription | None = None,
    ) -> None:
        super().__init__(id)
        self._name = SchedulerName(name) if isinstance(name, str) else name
        self._description = (
            SchedulerDescription(description) if isinstance(description, str) else description
        )
        self._trigger_config = trigger_config
        self._action_config = action_config
        self._execution_policy = execution_policy
        self._enabled = enabled if isinstance(enabled, Enabled) else Enabled(enabled)
        self._created_at = created_at
        self._updated_at = updated_at

    @classmethod
    def restore(
        cls,
        id: SchedulerDefinitionId,
        name: SchedulerName,
        enabled: Enabled,
        trigger_config: TriggerConfig,
        action_config: ActionConfig,
        execution_policy: ExecutionPolicy,
        created_at: CreatedAt,
        updated_at: Timestamp,
        description: SchedulerDescription | None = None,
    ) -> Self:
        return cls(
            id=id,
            name=name,
            description=description,
            enabled=enabled,
            trigger_config=trigger_config,
            action_config=action_config,
            execution_policy=execution_policy,
            created_at=created_at,
            updated_at=updated_at,
        )

    @classmethod
    def _new(
        cls,
        *,
        id_: SchedulerDefinitionId,
        name: SchedulerName,
        trigger_config: TriggerConfig,
        action_config: ActionConfig,
        execution_policy: ExecutionPolicy,
        now: CreatedAt,
        enabled: bool = True,
        description: SchedulerDescription | None = None,
    ) -> SchedulerDefinition:
        instance = cls(
            id=id_,
            name=name,
            enabled=Enabled(enabled),
            trigger_config=trigger_config,
            action_config=action_config,
            execution_policy=execution_policy,
            created_at=now,

            description=description,
        )
        instance.append_event(
            SchedulerDefinitionCreatedEvent.now(
                scheduler_definition_id=instance.id,
                now=now,
            )
        )
        return instance

    @classmethod
    def create(
        cls,
        *,
        id_: SchedulerDefinitionId,
        name: SchedulerName,
        trigger_config: TriggerConfig,
        action_config: ActionConfig,
        execution_policy: ExecutionPolicy,
        now: CreatedAt,
        enabled: bool = True,
        description: SchedulerDescription | None = None,
    ) -> SchedulerDefinition:
        return cls._new(
            id_=id_,
            name=name,
            trigger_config=trigger_config,
            action_config=action_config,
            execution_policy=execution_policy,
            now=now,
            enabled=enabled,
            description=description,
        )

    @property
    def name(self) -> SchedulerName:
        return self._name

    @property
    def description(self) -> SchedulerDescription | None:
        return self._description

    @property
    def trigger_config(self) -> TriggerConfig:
        return self._trigger_config

    @property
    def action_config(self) -> ActionConfig:
        return self._action_config

    @property
    def execution_policy(self) -> ExecutionPolicy:
        return self._execution_policy

    @property
    def enabled(self) -> Enabled:
        return self._enabled

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def updated_at(self) -> Timestamp:
        return self._updated_at

    def matches_trigger(self, source_context: str, trigger_event_type: str) -> bool:
        return (
            self._enabled.value
            and self._trigger_config.source_context == source_context
            and self._trigger_config.trigger_event_type == trigger_event_type
        )
