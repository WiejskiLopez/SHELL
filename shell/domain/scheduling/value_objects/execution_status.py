from __future__ import annotations

from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class ExecutionStatus(ValueObject):
    value: str

    def __str__(self) -> str:
        return self.value


ExecutionStatus.PENDING = ExecutionStatus("pending")
ExecutionStatus.SKIPPED = ExecutionStatus("skipped")
ExecutionStatus.EXECUTING = ExecutionStatus("executing")
ExecutionStatus.COMPLETED = ExecutionStatus("completed")
ExecutionStatus.FAILED = ExecutionStatus("failed")
