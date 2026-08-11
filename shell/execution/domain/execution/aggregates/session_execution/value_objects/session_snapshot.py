from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.base.value_object import ValueObject
from shell.platform.domain.exceptions.domain_error import DomainError

if TYPE_CHECKING:
    from shell.execution.domain.execution.aggregates.session_execution.value_objects.session_id_ref import (
        SessionIdRef,
    )
    from shell.platform.domain.value_objects.timestamp import Timestamp


@dataclass(frozen=True, slots=True)
class SessionSnapshot(ValueObject):
    """Snapshot of a Session from the session BC, owned by the execution BC."""

    session_id: SessionIdRef
    goal: str
    status: str
    opened_at: Timestamp
    closed_at: Timestamp | None
    created_at: Timestamp

    def __post_init__(self) -> None:
        if not self.goal:
            raise DomainError("SessionSnapshot goal cannot be empty")
        if not self.status:
            raise DomainError("SessionSnapshot status cannot be empty")
