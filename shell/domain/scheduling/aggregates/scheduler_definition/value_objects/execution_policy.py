from __future__ import annotations

from dataclasses import dataclass

from shell.platform.domain.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class ExecutionPolicy(ValueObject):
    max_concurrent: int = 1
    timeout_seconds: int | None = None
    retry_count: int = 0
    retry_delay_seconds: int = 0

    def __post_init__(self) -> None:
        if self.max_concurrent < 1:
            raise DomainError("ExecutionPolicy.max_concurrent must be >= 1")
        if self.timeout_seconds is not None and self.timeout_seconds < 0:
            raise DomainError("ExecutionPolicy.timeout_seconds cannot be negative")
        if self.retry_count < 0:
            raise DomainError("ExecutionPolicy.retry_count cannot be negative")
        if self.retry_delay_seconds < 0:
            raise DomainError("ExecutionPolicy.retry_delay_seconds cannot be negative")

    def __str__(self) -> str:
        parts = [f"max_concurrent={self.max_concurrent}"]
        if self.timeout_seconds is not None:
            parts.append(f"timeout={self.timeout_seconds}s")
        return f"ExecutionPolicy({', '.join(parts)})"
