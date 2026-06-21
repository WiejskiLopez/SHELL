from __future__ import annotations

import uuid
from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class RunnerConfigId(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("RunnerConfigId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> RunnerConfigId:
        return cls(str(uuid.uuid4()))
