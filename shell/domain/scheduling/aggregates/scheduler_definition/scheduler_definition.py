from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.scheduling.aggregates.scheduler_definition.events.scheduler_definition_created_event import (
    SchedulerDefinitionCreatedEvent,
)
from shell.domain.scheduling.aggregates.scheduler_definition.events.scheduler_definition_deleted_event import (
    SchedulerDefinitionDeletedEvent,
)
from shell.domain.scheduling.aggregates.scheduler_definition.events.scheduler_definition_updated_event import (
    SchedulerDefinitionUpdatedEvent,
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
from shell.platform.domain.exceptions import DomainError
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.enabled import Enabled
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt

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
        "_created_at",
        "_updated_at",
        "_deleted_at",
        "_name",
        "_description",
        "_trigger_config",
        "_action_config",
        "_execution_policy",
        "_enabled",
    )

    def __init__(
        self,
        *,
        id: SchedulerDefinitionId,
        created_at: CreatedAt,
        updated_at: UpdatedAt | None = None,
        name: SchedulerName,
        enabled: Enabled,
        trigger_config: TriggerConfig,
        action_config: ActionConfig,
        execution_policy: ExecutionPolicy,
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
        self._updated_at = UpdatedAt(value=None) if updated_at is None else updated_at
        self._deleted_at = DeletedAt(value=None)

    @classmethod
    def restore(
        cls,
        *,
        id: SchedulerDefinitionId,
        created_at: CreatedAt,
        updated_at: UpdatedAt | None = None,
        name: SchedulerName,
        enabled: Enabled,
        trigger_config: TriggerConfig,
        action_config: ActionConfig,
        execution_policy: ExecutionPolicy,
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
        now: OccurredAt,
        name: SchedulerName,
        trigger_config: TriggerConfig,
        action_config: ActionConfig,
        execution_policy: ExecutionPolicy,
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
            created_at=CreatedAt.from_datetime(now.value),
            description=description,
        )
        instance.append_event(
            SchedulerDefinitionCreatedEvent.now(
                scheduler_definition_id=instance.id,
                now=OccurredAt.from_datetime(now.value),
            )
        )
        return instance

    @classmethod
    def create(
        cls,
        *,
        id_: SchedulerDefinitionId,
        now: CreatedAt,
        name: SchedulerName,
        trigger_config: TriggerConfig,
        action_config: ActionConfig,
        execution_policy: ExecutionPolicy,
        enabled: bool = True,
        description: SchedulerDescription | None = None,
    ) -> SchedulerDefinition:
        return cls._new(
            id_=id_,
            name=name,
            trigger_config=trigger_config,
            action_config=action_config,
            execution_policy=execution_policy,
            now=OccurredAt.from_datetime(now.value),
            enabled=enabled,
            description=description,
        )

    def delete(self, now: DeletedAt) -> None:
        if self._deleted_at is not None and self._deleted_at.value is not None:
            raise DomainError("Scheduler definition already deleted")
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            SchedulerDefinitionDeletedEvent.now(
                scheduler_definition_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def update(self, now: UpdatedAt) -> None:
        if self._deleted_at is not None and self._deleted_at.value is not None:
            raise DomainError("Scheduler definition already deleted")
        self._updated_at = now
        self.append_event(
            SchedulerDefinitionUpdatedEvent.now(
                scheduler_definition_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            SchedulerDefinitionDeletedEvent.now(
                scheduler_definition_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            SchedulerDefinitionUpdatedEvent.now(
                scheduler_definition_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
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
    def updated_at(self) -> UpdatedAt:
        return self._updated_at

    def matches_trigger(self, source_context: str, trigger_event_type: str) -> bool:
        return (
            self._enabled.value
            and self._trigger_config.source_context == source_context
            and self._trigger_config.trigger_event_type == trigger_event_type
        )
