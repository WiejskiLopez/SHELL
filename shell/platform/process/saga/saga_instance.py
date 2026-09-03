"""SagaInstance — niezmienniczy rekord stanu instancji sagi (trwały).

To obiekt wymieniany między warstwą process a infrastrukturą (repozytorium).
Kopiowany przy przejściach; nigdy niemutowalny po utworzeniu.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from shell.platform.process.saga.base.saga_state import SagaStatus


@dataclass(frozen=True, slots=True)
class SagaInstance:
    """Immutable snapshot stanu sagi dla warstwy persistence."""

    saga_id: str
    saga_type: str
    saga_key: str
    status: SagaStatus
    business_payload: dict[str, object] = field(default_factory=dict)
    completed_steps: tuple[str, ...] = ()
    failed_steps: tuple[str, ...] = ()
    current_step: str | None = None
    version: int = 1
    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None
    compensated_at: datetime | None = None
