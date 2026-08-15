from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.definition_service.domain.definition.aggregates.runner_config.value_objects.runner_config_id import (
        RunnerConfigId,
    )
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True)
class RunnerConfigDeletedEvent(DomainEvent):
    runner_config_id: RunnerConfigId

    @classmethod
    def now(cls, runner_config_id: RunnerConfigId, now: OccurredAt) -> RunnerConfigDeletedEvent:
        return cls(occurred_at=now, runner_config_id=runner_config_id)
