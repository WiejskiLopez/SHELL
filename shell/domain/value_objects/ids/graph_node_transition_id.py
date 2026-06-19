from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GraphNodeTransitionId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("GraphNodeTransitionId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> GraphNodeTransitionId:
        return cls(str(uuid.uuid4()))
