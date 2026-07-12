"""SemanticData value object — semantic query with opaque JSON payload.

Single-field ValueObject wrapping a JsonStr. The structure of
the JSON is defined by the consuming bounded context —
SemanticData only ensures it is valid JSON.
"""

from __future__ import annotations

from dataclasses import dataclass

from shell.platform.domain.base.value_object import ValueObject
from shell.platform.types import (  # noqa: TC001 — used in dataclass field
    JsonStr,
)


@dataclass(frozen=True, slots=True)
class SemanticData(ValueObject):
    value: JsonStr

    def to_dict(self) -> str:
        return self.value.value

    def __str__(self) -> str:
        return str(self.value)
