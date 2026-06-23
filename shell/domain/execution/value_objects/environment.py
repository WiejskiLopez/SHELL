from __future__ import annotations

from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class Environment(ValueObject):
    os: str
    runtime: str
    cwd: str
