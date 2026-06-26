from __future__ import annotations

from dataclasses import dataclass

from shell.domain.platform.base import ValueObject


@dataclass(frozen=True, slots=True)
class IsCurrent(ValueObject):
    value: bool
