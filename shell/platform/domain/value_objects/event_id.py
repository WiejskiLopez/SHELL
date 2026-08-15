"""EventId value object for domain event identifiers."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Self

from shell.platform.domain.base.entity_id import EntityId


@dataclass(frozen=True, slots=True)
class EventId(EntityId):
    value: str

    @classmethod
    def generate(cls) -> Self:
        return cls(str(uuid.uuid4()))
