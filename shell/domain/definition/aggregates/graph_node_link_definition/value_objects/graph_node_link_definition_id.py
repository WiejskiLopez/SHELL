from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class GraphNodeLinkDefinitionId(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("GraphNodeLinkDefinitionId cannot be empty")

    @classmethod
    def generate(cls) -> GraphNodeLinkDefinitionId:
        return cls(str(uuid4()))
