from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetNodeDefinitionByIdQuery:
    node_definition_id: str
