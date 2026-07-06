from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class NodeExecutionStateDto:
    node_execution_id: str
    status: str
    step: int
    updated_at: datetime
