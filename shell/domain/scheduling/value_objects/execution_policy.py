from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExecutionPolicy:
    max_concurrent: int = 1
    timeout_seconds: int | None = None
    retry_count: int = 0
    retry_delay_seconds: int = 0
