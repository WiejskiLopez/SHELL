from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GraphDefinitionDto:
    id: str
    name: str
    purpose: str
