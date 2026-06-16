"""ExecutionResult value object — subprocess output."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    returncode: int
    stdout: str = field(default="")
    stderr: str = field(default="")

    @property
    def success(self) -> bool:
        return self.returncode == 0
