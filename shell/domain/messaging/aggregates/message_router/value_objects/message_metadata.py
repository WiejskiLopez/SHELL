from __future__ import annotations

from dataclasses import dataclass, field

from shell.platform.domain.base.value_object import ValueObject
from shell.platform.types import (  # noqa: TC001 — potrzebny w default_factory
    JsonStr,
)


@dataclass(frozen=True, slots=True)
class MessageMetadata(ValueObject):
    value: JsonStr = field(default_factory=lambda: JsonStr("{}"))
