from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True, kw_only=True)
class AuthSessionLoginFailedEvent(DomainEvent):
    @classmethod
    def now(
        cls,
        *,
        now: OccurredAt,
    ) -> AuthSessionLoginFailedEvent:
        return cls(occurred_at=now)
