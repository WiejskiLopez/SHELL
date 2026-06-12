from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetNodeResultQuery:
    node_id: str
    workflow_id: str
