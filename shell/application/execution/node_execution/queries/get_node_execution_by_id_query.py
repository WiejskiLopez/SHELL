from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetNodeExecutionByIdQuery:
    node_execution_id: str
