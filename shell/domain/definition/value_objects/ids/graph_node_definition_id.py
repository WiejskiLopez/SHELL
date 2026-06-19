from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GraphNodeDefinitionId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("GraphNodeDefinitionId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> GraphNodeDefinitionId:
        return cls(str(uuid.uuid4()))
