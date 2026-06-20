from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ExecutionStatus:
    value: str

    def __str__(self) -> str:
        return self.value


ExecutionStatus.PENDING = ExecutionStatus("pending")
ExecutionStatus.SKIPPED = ExecutionStatus("skipped")
ExecutionStatus.EXECUTING = ExecutionStatus("executing")
ExecutionStatus.COMPLETED = ExecutionStatus("completed")
ExecutionStatus.FAILED = ExecutionStatus("failed")
