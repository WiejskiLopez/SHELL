from __future__ import annotations

from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionResultId(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("GraphNodeExecutionResultId cannot be empty")

    @classmethod
    def generate(cls) -> GraphNodeExecutionResultId:
        import uuid
        return cls(str(uuid.uuid4()))

    def __str__(self) -> str:
        return self.value
