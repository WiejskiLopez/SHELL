"""ExecutionResult value object — subprocess output."""

from __future__ import annotations

from dataclasses import dataclass, field

from shell.platform.domain.base.value_object import ValueObject
from shell.platform.domain.exceptions.domain_error import DomainError


@dataclass(frozen=True, slots=True)
class ExecutionResult(ValueObject):
    returncode: int
    stdout: str = field(default="")
    stderr: str = field(default="")

    def __post_init__(self) -> None:
        if not isinstance(self.returncode, int):
            raise DomainError("ExecutionResult.returncode must be an int")

    def __str__(self) -> str:
        return f"ExecutionResult(returncode={self.returncode})"

    @property
    def success(self) -> bool:
        return self.returncode == 0
