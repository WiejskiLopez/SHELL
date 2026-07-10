from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from shell.platform.domain.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class NodeLinkExecutionId(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("NodeLinkExecutionId cannot be empty")

    @classmethod
    def generate(cls) -> NodeLinkExecutionId:
        return cls(str(uuid4()))
