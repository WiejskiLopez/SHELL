"""MessageId value object for domain message identifiers."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Self

from shell.platform.domain.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class MessageId(ValueObject):
    value: str

    @classmethod
    def generate(cls) -> Self:
        return cls(str(uuid.uuid4()))
