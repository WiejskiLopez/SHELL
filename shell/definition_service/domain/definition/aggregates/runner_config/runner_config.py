from __future__ import annotations

from typing import Self

from shell.definition_service.domain.definition.aggregates.runner_config.events.runner_config_changed_event import (
    RunnerConfigChangedEvent,
)
from shell.definition_service.domain.definition.aggregates.runner_config.events.runner_config_created_event import (
    RunnerConfigCreatedEvent,
)
from shell.definition_service.domain.definition.aggregates.runner_config.events.runner_config_deleted_event import (
    RunnerConfigDeletedEvent,
)
from shell.definition_service.domain.definition.aggregates.runner_config.value_objects.runner_config_id import (
    RunnerConfigId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.changed_at import NONE_CHANGED_AT, ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt


class RunnerConfig(AggregateRoot[RunnerConfigId]):
    __slots__ = (
        "_created_at",
        "_changed_at",
        "_deleted_at",
    )

    _changed_at: ChangedAt
    _deleted_at: DeletedAt

    def __init__(
        self,
        id: RunnerConfigId,
        created_at: CreatedAt,
    ) -> None:
        super().__init__(id)
        self._created_at = (
            created_at if isinstance(created_at, CreatedAt) else CreatedAt(created_at)
        )
        self._changed_at = NONE_CHANGED_AT
        self._deleted_at = NONE_DELETED_AT

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self.append_event(
            RunnerConfigDeletedEvent.now(
                runner_config_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _change(self, now: OccurredAt) -> None:
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            RunnerConfigChangedEvent.now(
                runner_config_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def changed_at(self) -> ChangedAt:
        return self._changed_at

    @classmethod
    def _new(
        cls,
        *,
        id_: RunnerConfigId,
        now: OccurredAt,
    ) -> RunnerConfig:
        instance = cls(
            id=id_,
            created_at=CreatedAt.from_datetime(now.value),
        )
        instance.append_event(
            RunnerConfigCreatedEvent.now(
                runner_config_id=instance.id,
                now=OccurredAt.from_datetime(now.value),
            )
        )
        return instance

    @classmethod
    def create(
        cls,
        *,
        id_: RunnerConfigId,
        now: CreatedAt,
    ) -> RunnerConfig:
        return cls._new(id_=id_, now=OccurredAt.from_datetime(now.value))

    @classmethod
    def restore(
        cls,
        *,
        id: RunnerConfigId,
        created_at: CreatedAt,
    ) -> Self:
        return cls(
            id=id,
            created_at=created_at,
        )
