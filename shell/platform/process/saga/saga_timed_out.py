"""SagaTimedOut — sygnał procesora timeoutów do handlery sagi."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SagaTimedOut:
    """Fakt: krok sagi nie doczekał się rezultatu przed upływem czasu."""

    saga_id: str
    saga_key: str
    step: str
    payload: dict[str, object] = field(default_factory=dict)
