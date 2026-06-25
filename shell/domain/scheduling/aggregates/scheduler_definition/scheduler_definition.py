from __future__ import annotations

from datetime import datetime

from shell.domain.platform.base import AggregateRoot
from shell.domain.scheduling.value_objects.action_config import ActionConfig
from shell.domain.scheduling.value_objects.execution_policy import ExecutionPolicy
from shell.domain.scheduling.value_objects.ids import SchedulerDefinitionId
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
        name: str,
        description: str | None = None,
        trigger_config: TriggerConfig | None = None,
        action_config: ActionConfig | None = None,
        execution_policy: ExecutionPolicy | None = None,
        enabled: bool = True,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        super().__init__(id)
        self._name = name
        self._description = description
        self._trigger_config = trigger_config or TriggerConfig(
            source_context="", trigger_event_type=""
        )
        self._action_config = action_config or ActionConfig(action_type="")
        self._execution_policy = execution_policy or ExecutionPolicy()
        self._enabled = enabled
        self._created_at = created_at or datetime.now()
        self._updated_at = updated_at or datetime.now()

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str | None:
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
    def enabled(self) -> bool:
        return self._enabled

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    def matches_trigger(self, source_context: str, trigger_event_type: str) -> bool:
        return (
            self._enabled
            and self._trigger_config.source_context == source_context
            and self._trigger_config.trigger_event_type == trigger_event_type
        )
