"""Status value object.

.. deprecated::
   Use dedicated status enums (TaskExecutionStatus, GraphNodeExecutionStatus, WorkflowStatus)
   from shell.domain.execution.value_objects for new code.
"""

from __future__ import annotations

from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class Status(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Status cannot be empty")

    def __str__(self) -> str:
        return self.value

    # Common sentinel values
    @classmethod
    def idle(cls) -> Status:
        return cls("idle")

    @classmethod
    def running(cls) -> Status:
        return cls("running")

    @classmethod
    def done(cls) -> Status:
        return cls("done")

    @classmethod
    def failed(cls) -> Status:
        return cls("failed")

    @classmethod
    def waiting(cls) -> Status:
        return cls("waiting")
