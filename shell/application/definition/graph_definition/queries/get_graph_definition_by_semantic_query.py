from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetGraphDefinitionBySemanticQuery:
    query: str
    purpose: str | None = None
    limit: int = 1
    default_graph_definition_id: str | None = None
