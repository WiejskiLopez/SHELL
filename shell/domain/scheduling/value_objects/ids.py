from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SchedulerDefinitionId:
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
class SchedulerExecutionId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("SchedulerExecutionId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> SchedulerExecutionId:
        return cls(str(uuid.uuid4()))
