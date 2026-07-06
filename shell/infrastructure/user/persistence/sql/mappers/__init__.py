"""SQL ORM model <-> domain entity mappers for User BC."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.deleted_at import DeletedAt
from shell.domain.platform.value_objects.state_data import StateData
from shell.domain.platform.value_objects.state_direction import StateDirection
from shell.domain.platform.value_objects.updated_at import UpdatedAt
from shell.domain.user.aggregates.user.user import User
from shell.domain.user.aggregates.user_skill.user_skill import UserSkill
from shell.domain.user.aggregates.user_state.user_state import UserState
from shell.domain.user.aggregates.user_state.value_objects.user_state_id import UserStateId
from shell.domain.user.value_objects.skill_data import SkillData
from shell.domain.user.value_objects.skill_id import SkillId
from shell.domain.user.value_objects.user_email import UserEmail
from shell.domain.user.value_objects.user_id import UserId
from shell.domain.user.value_objects.user_status import UserStatus
from shell.infrastructure.user.user.persistence.sql.models.user import UserModel
from shell.infrastructure.user.user_skill.persistence.sql.models.user_skill import UserSkillModel
from shell.infrastructure.user.user_state.persistence.sql.models.user_state import UserStateModel


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


# ── User ────────────────────────────────────────────────────────────────────────


def user_model_to_entity(model: UserModel) -> User:
    return User.restore(
        id=UserId(model.id),
        email=UserEmail(model.email),
        status=UserStatus(model.status),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
        updated_at=UpdatedAt.from_datetime(_ensure_utc(model.updated_at))
        if model.updated_at is not None
        else None,
        deleted_at=DeletedAt.from_datetime(_ensure_utc(model.deleted_at))
        if model.deleted_at is not None
        else None,
    )


def user_entity_to_model(entity: User) -> UserModel:
    return UserModel(
        id=entity.id.value,
        email=entity.email.value,
        status=entity.status.value,
        created_at=entity.created_at.value if entity.created_at else None,
        updated_at=entity.updated_at.value if entity.updated_at else None,
        deleted_at=entity.deleted_at.value if entity.deleted_at else None,
    )


def user_update_model(model: UserModel, entity: User) -> None:
    model.email = entity.email.value
    model.status = entity.status.value
    assert entity.created_at is not None
    model.created_at = entity.created_at.value
    model.updated_at = entity.updated_at.value if entity.updated_at else None  # type: ignore[assignment]
    model.deleted_at = entity.deleted_at.value if entity.deleted_at else None


# ── UserSkill ────────────────────────────────────────────────────────────────────


def user_skill_model_to_entity(model: UserSkillModel) -> UserSkill:
    return UserSkill.restore(
        id=SkillId(model.id),
        user_id=UserId(model.user_id),
        skill_data=SkillData(dict(model.skill_data)) if model.skill_data else SkillData({}),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def user_skill_entity_to_model(entity: UserSkill) -> UserSkillModel:
    return UserSkillModel(
        id=entity.id.value,
        user_id=entity.user_id.value,
        skill_data=entity.skill_data.to_dict(),
        created_at=entity.created_at.value if entity.created_at else None,
    )


# ── UserState ────────────────────────────────────────────────────────────────────


def user_state_model_to_entity(model: UserStateModel) -> UserState:
    return UserState.restore(
        id=UserStateId(model.id),
        user_id=UserId(model.user_id),
        direction=StateDirection(model.direction),
        state_data=StateData(dict(model.state_data)) if model.state_data else StateData({}),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def user_state_entity_to_model(entity: UserState) -> UserStateModel:
    return UserStateModel(
        id=entity.id.value,
        user_id=entity.user_id.value,
        direction=entity.direction.value,
        state_data=entity.snapshot(),
        created_at=entity.created_at.value if entity.created_at else None,
    )
