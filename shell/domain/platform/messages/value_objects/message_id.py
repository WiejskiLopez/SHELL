from __future__ import annotations

import uuid
from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class MessageId(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("MessageId cannot be empty")

    @classmethod
    def generate(cls) -> MessageId:
        return cls(str(uuid.uuid4()))

    def __str__(self) -> str:
        return self.value
