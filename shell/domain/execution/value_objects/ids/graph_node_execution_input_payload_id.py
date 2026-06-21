from __future__ import annotations

import uuid
from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionInputPayloadId(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("GraphNodeExecutionInputPayloadId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> GraphNodeExecutionInputPayloadId:
        return cls(str(uuid.uuid4()))
