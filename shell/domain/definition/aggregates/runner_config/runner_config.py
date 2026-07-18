from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.definition.aggregates.runner_config.events.runner_config_created_event import (
    RunnerConfigCreatedEvent,
)
from shell.domain.definition.aggregates.runner_config.events.runner_config_deleted_event import (
    RunnerConfigDeletedEvent,
)
from shell.domain.definition.aggregates.runner_config.events.runner_config_updated_event import (
    RunnerConfigUpdatedEvent,
)
from shell.domain.definition.aggregates.runner_config.value_objects.runner_config_id import (
    RunnerConfigId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.deleted_at import DeletedAt
    from shell.platform.domain.value_objects.updated_at import UpdatedAt


class RunnerConfig(AggregateRoot[RunnerConfigId]):
    __slots__ = (
        "_updated_at","_created_at",)

    def __init__(
        self,
        id: RunnerConfigId,
        created_at: CreatedAt,
    ) -> None:
        super().__init__(id)
        self._created_at = (
            created_at if isinstance(created_at, CreatedAt) else CreatedAt(created_at)
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self.append_event(
            RunnerConfigDeletedEvent.now(
                runnerconfig_id=self._id,
                now=CreatedAt.from_datetime(now.value),
            )
        )
    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            RunnerConfigUpdatedEvent.now(
                runnerconfig_id=self._id,
                now=CreatedAt.from_datetime(now.value),
            )
        )
    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @classmethod
    def _new(
        cls,
        *,
        id_: RunnerConfigId,
        now: CreatedAt,
    ) -> RunnerConfig:
        instance = cls(
            id=id_,
            created_at=now,
        )
        instance.append_event(
            RunnerConfigCreatedEvent.now(
                runnerconfig_id=instance.id,
                now=now,
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
        return cls._new(id_=id_, now=now)

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
