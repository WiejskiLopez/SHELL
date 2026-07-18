from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.runner_config.value_objects.RunnerConfigId import RunnerConfigId
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class RunnerConfigUpdatedEvent(DomainEvent):
    runnerconfig_id: RunnerConfigId

    @classmethod
    def now(cls, runnerconfig_id: RunnerConfigId, now: CreatedAt) -> "RunnerConfigUpdatedEvent":
        return cls(occurred_at=now, runnerconfig_id=runnerconfig_id)
