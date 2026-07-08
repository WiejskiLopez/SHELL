from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class MessageDto:
    id: str
    message_type: str
    business_payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    destination: str = ""
    status: str = "created"
    workflow_id: str | None = None
    step: int | None = None
    sequence_id: int | None = None
    source_node_execution_id: str | None = None
    target_node_execution_id: str | None = None
    source_role: str | None = None
    target_role: str | None = None
    created_at: datetime | None = None
    received_at: datetime | None = None
