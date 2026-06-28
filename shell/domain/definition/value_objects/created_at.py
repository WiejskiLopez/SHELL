from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class CreatedAt(ValueObject):
    value: datetime

    def __str__(self) -> str:
        return self.value.isoformat()
