from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NodeExecutionGetByIdQuery:
    node_execution_id: str
