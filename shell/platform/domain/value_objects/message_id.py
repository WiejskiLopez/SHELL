"""MessageId value object for domain message identifiers."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Self

from shell.platform.domain.base.entity_id import EntityId


@dataclass(frozen=True, slots=True)
class MessageId(EntityId):
    value: str

    @classmethod
    def generate(cls) -> Self:
        return cls(str(uuid.uuid4()))
