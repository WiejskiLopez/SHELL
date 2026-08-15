from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetEdgeLinkExecutionByIdQuery:
    edge_link_execution_id: str
