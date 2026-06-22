from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.session.session_id import SessionId
from shell.domain.platform.base.aggregate_root import AggregateRoot

if TYPE_CHECKING:
    from datetime import datetime


class Session(AggregateRoot[SessionId]):
    __slots__ = ("goal", "status", "opened_at", "closed_at")

    def __init__(
        self,
        id: SessionId,
        goal: str,
        status: str,
        opened_at: datetime,
        closed_at: datetime | None,
    ) -> None:
        if not goal:
            raise ValueError("goal cannot be empty")
        if status not in ("open", "closed"):
            raise ValueError(f"invalid status: {status!r}")
        super().__init__(id)
        self.goal = goal
        self.status = status
        self.opened_at = opened_at
        self.closed_at = closed_at

    @classmethod
    def open(
        cls,
        id_: SessionId,
        goal: str,
        now: datetime,
    ) -> Session:
        return cls(
            id=id_,
            goal=goal,
            status="open",
            opened_at=now,
            closed_at=None,
        )

    def close(self, now: datetime) -> None:
        if self.status == "closed":
            raise ValueError("Session already closed")
        self.status = "closed"
        self.closed_at = now
