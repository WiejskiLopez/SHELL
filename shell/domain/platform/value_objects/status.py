"""Status value object — node/workflow/envelope runtime status string."""

from __future__ import annotations

import warnings
from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject

warnings.warn(
    "Status is deprecated — use dedicated status enums from shell.domain.execution.value_objects instead.",
    DeprecationWarning,
    stacklevel=2,
)


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
