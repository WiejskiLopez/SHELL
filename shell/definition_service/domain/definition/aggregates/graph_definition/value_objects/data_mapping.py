from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.base.value_object import ValueObject

if TYPE_CHECKING:
    from shell.platform.types import JsonStr


@dataclass(frozen=True, slots=True)
class DataMapping(ValueObject):
    value: JsonStr

    def __str__(self) -> str:
        return str(self.value)
