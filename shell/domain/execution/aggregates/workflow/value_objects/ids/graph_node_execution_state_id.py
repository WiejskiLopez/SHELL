from __future__ import annotations

import uuid
from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionStateId(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("GraphNodeExecutionStateId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> GraphNodeExecutionStateId:
        return cls(str(uuid.uuid4()))
