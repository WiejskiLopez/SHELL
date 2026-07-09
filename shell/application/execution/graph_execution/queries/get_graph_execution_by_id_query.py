from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetGraphExecutionByIdQuery:
    graph_execution_id: str
