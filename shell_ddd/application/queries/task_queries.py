from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetTaskByNameQuery:
    name: str


@dataclass(frozen=True, slots=True)
class GetCurrentTaskQuery:
    name: str
