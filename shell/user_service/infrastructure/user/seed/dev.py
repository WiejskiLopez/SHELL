"""Development seed data for the User bounded context.

Idempotent: records are inserted only when missing, so the seed can be
run repeatedly against the same database without creating duplicates.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.user_service.infrastructure.user.seed.builders import (
    build_user_model,
    build_user_skill_model,
    build_user_state_model,
)
from shell.user_service.infrastructure.user.user.persistence.sql.models.user import UserModel

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

DEV_ID_PREFIX = "dev"

_USERS_DATA: list[dict[str, str]] = [
    {"id": f"{DEV_ID_PREFIX}-user-alice", "email": "alice@example.com", "status": "active"},
    {"id": f"{DEV_ID_PREFIX}-user-bob", "email": "bob@example.com", "status": "active"},
    {"id": f"{DEV_ID_PREFIX}-user-charlie", "email": "charlie@example.com", "status": "inactive"},
]


def seed_dev_sync(session: Session) -> None:
    """Insert dev users with their states and skills when missing."""
    for user_data in _USERS_DATA:
        existing_user = session.execute(
            select(UserModel).where(UserModel.id == user_data["id"])
        ).scalar_one_or_none()
        if existing_user is not None:
            continue

        session.add(
            build_user_model(
                user_id=user_data["id"],
                email=user_data["email"],
                status=user_data["status"],
            )
        )

        for direction in ("INPUT", "OUTPUT"):
            session.add(
                build_user_state_model(
                    state_id=f"{user_data['id']}-state-{direction.lower()}",
                    user_id=user_data["id"],
                    direction=direction,
                    state_data={"info": f"{direction.lower()} state for {user_data['email']}"},
                )
            )

        for skill_index in (1, 2):
            level = "advanced" if skill_index == 1 else "intermediate"
            session.add(
                build_user_skill_model(
                    skill_id=f"{user_data['id']}-skill-{skill_index}",
                    user_id=user_data["id"],
                    skill_data={"name": f"skill-{skill_index}", "level": level},
                )
            )


__all__ = ["DEV_ID_PREFIX", "seed_dev_sync"]
