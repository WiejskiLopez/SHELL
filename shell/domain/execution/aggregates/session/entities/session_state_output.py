from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.session.value_objects.session_id import SessionId

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class SessionStateOutput:
    id: SessionId
    session_id: SessionId
    payload: dict
    created_at: datetime
