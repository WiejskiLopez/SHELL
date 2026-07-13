from __future__ import annotations

from typing import Self

from shell.domain.definition.aggregates.runner_config.value_objects.runner_config_id import (
    RunnerConfigId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.created_at import CreatedAt


class RunnerConfig(AggregateRoot[RunnerConfigId]):
    __slots__ = ("_created_at",)

    def __init__(
        self,
        id: RunnerConfigId,
        created_at: CreatedAt,
    ) -> None:
        super().__init__(id)
        self._created_at = (
            created_at if isinstance(created_at, CreatedAt) else CreatedAt(created_at)
        )

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @classmethod
    def new(
        cls,
        *,
        id_: RunnerConfigId,
        now: CreatedAt,
    ) -> RunnerConfig:
        return cls(
            id=id_,
            created_at=now,
        )

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
