from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TaskExecutionOutputPayloadId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("TaskExecutionOutputPayloadId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> TaskExecutionOutputPayloadId:
        return cls(str(uuid.uuid4()))
