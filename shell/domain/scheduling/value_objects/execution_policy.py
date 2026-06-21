from __future__ import annotations

from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class ExecutionPolicy(ValueObject):
    max_concurrent: int = 1
    timeout_seconds: int | None = None
    retry_count: int = 0
    retry_delay_seconds: int = 0
