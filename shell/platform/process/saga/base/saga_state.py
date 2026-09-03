"""Typy stanu sagi — wspólne statusy i shape stanu biznesowego."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SagaStatus(StrEnum):
    """Status cyklu życia instancji sagi."""

    RUNNING = "running"
    FAILING = "failing"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class SagaState:
    """Trwały stan sagi (business payload przechowywany osobno w instancji)."""

    status: SagaStatus
    current_step: str | None = None
    completed_steps: tuple[str, ...] = ()
    failed_steps: tuple[str, ...] = ()
