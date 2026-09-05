from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SagaStatus(StrEnum):
    RUNNING = "running"
    FAILING = "failing"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class SagaState:
    status: SagaStatus
    current_step: str | None = None
    completed_steps: tuple[str, ...] = ()
    failed_steps: tuple[str, ...] = ()
