from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetTaskExecutionByNameQuery:
    name: str


@dataclass(frozen=True, slots=True)
class GetCurrentTaskExecutionQuery:
    name: str
