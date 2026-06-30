from __future__ import annotations

from typing import Self

from shell.domain.platform.base import AggregateRoot
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.enabled import Enabled
from shell.domain.platform.value_objects.timestamp import Timestamp
from shell.domain.scheduling.value_objects.action_config import ActionConfig
from shell.domain.scheduling.value_objects.execution_policy import ExecutionPolicy
from shell.domain.scheduling.value_objects.ids import SchedulerDefinitionId
from shell.domain.scheduling.value_objects.scheduler_description import (
    SchedulerDescription,
)
from shell.domain.scheduling.value_objects.scheduler_name import SchedulerName
from shell.domain.scheduling.value_objects.trigger_config import TriggerConfig


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
        description: SchedulerDescription | None = None,
        trigger_config: TriggerConfig | None = None,
        action_config: ActionConfig | None = None,
        execution_policy: ExecutionPolicy | None = None,
        created_at: CreatedAt | None = None,
        updated_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id)
        self._name = SchedulerName(name) if isinstance(name, str) else name
        self._description = (
            SchedulerDescription(description) if isinstance(description, str) else description
        )
        self._trigger_config = trigger_config or TriggerConfig(
            source_context="", trigger_event_type=""
        )
        self._action_config = action_config or ActionConfig(action_type="")
        self._execution_policy = execution_policy or ExecutionPolicy()
        self._enabled = enabled if isinstance(enabled, Enabled) else Enabled(enabled)
        self._created_at = created_at or CreatedAt.now()
        self._updated_at = updated_at or Timestamp.now()

    @classmethod
    def restore(
        cls,
        id: SchedulerDefinitionId,
        name: SchedulerName,
        enabled: Enabled,
        description: SchedulerDescription | None = None,
        trigger_config: TriggerConfig | None = None,
        action_config: ActionConfig | None = None,
        execution_policy: ExecutionPolicy | None = None,
        created_at: CreatedAt | None = None,
        updated_at: Timestamp | None = None,
    ) -> Self:
        return cls(
            id=id,
            name=name,
            description=description,
            trigger_config=trigger_config,
            action_config=action_config,
            execution_policy=execution_policy,
            enabled=enabled,
            created_at=created_at,
            updated_at=updated_at,
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
