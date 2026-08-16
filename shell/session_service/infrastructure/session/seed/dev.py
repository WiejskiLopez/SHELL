"""Development seed data for the Session bounded context.

Idempotent: records are inserted only when missing, so the seed can be
run repeatedly against the same database without creating duplicates.

Cross-BC user references use the shared ``dev-user-*`` ID convention
(user BC owns those records); they are opaque string IDs here.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.session_service.infrastructure.session.seed.builders import (
    build_session_model,
    build_session_state_model,
)
from shell.session_service.infrastructure.session.session.persistence.sql.models.session import (
    SessionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

DEV_ID_PREFIX = "dev"

_SESSIONS_DATA: list[dict[str, str]] = [
    {
        "id": f"{DEV_ID_PREFIX}-session-alice-1",
        "user_id": f"{DEV_ID_PREFIX}-user-alice",
        "goal": "Refactor authentication module",
        "status": "open",
    },
    {
        "id": f"{DEV_ID_PREFIX}-session-alice-2",
        "user_id": f"{DEV_ID_PREFIX}-user-alice",
        "goal": "Write API documentation",
        "status": "closed",
    },
    {
        "id": f"{DEV_ID_PREFIX}-session-bob-1",
        "user_id": f"{DEV_ID_PREFIX}-user-bob",
        "goal": "Optimize database queries",
        "status": "open",
    },
    {
        "id": f"{DEV_ID_PREFIX}-session-charlie-1",
        "user_id": f"{DEV_ID_PREFIX}-user-charlie",
        "goal": "Review pull requests",
        "status": "open",
    },
]


def seed_dev_sync(session: Session) -> None:
    """Insert dev sessions with their states when missing."""
    for session_data in _SESSIONS_DATA:
        existing_session = session.execute(
            select(SessionModel).where(SessionModel.id == session_data["id"])
        ).scalar_one_or_none()
        if existing_session is not None:
            continue

        is_closed = session_data["status"] == "closed"
        session.add(
            build_session_model(
                session_id=session_data["id"],
                user_id=session_data["user_id"],
                status=session_data["status"],
                closed_at=datetime.now(tz=UTC) if is_closed else None,
            )
        )

        for direction in ("INPUT", "OUTPUT"):
            session.add(
                build_session_state_model(
                    state_id=f"{session_data['id']}-state-{direction.lower()}",
                    session_id=session_data["id"],
                    direction=direction,
                    state_data={"goal": session_data["goal"], "step": direction.lower()},
                )
            )


__all__ = ["DEV_ID_PREFIX", "seed_dev_sync"]
