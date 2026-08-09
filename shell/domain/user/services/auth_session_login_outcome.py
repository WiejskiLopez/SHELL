from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.user.aggregates.auth_session.auth_session import AuthSession
    from shell.platform.domain.events import DomainEvent


@dataclass(frozen=True, slots=True)
class AuthSessionLoginOutcome:
    auth_session: AuthSession | None
    domain_events: tuple[DomainEvent, ...]
