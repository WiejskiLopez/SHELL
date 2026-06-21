from __future__ import annotations

import uuid
from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class SchedulerDefinitionId(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("SchedulerDefinitionId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> SchedulerDefinitionId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class SchedulerExecutionId(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("SchedulerExecutionId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> SchedulerExecutionId:
        return cls(str(uuid.uuid4()))
