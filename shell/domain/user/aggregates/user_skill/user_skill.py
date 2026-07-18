from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.user.aggregates.user_skill.events.user_skill_created_event import (
    UserSkillCreatedEvent,
)
from shell.domain.user.value_objects.skill_data import SkillData
from shell.domain.user.value_objects.skill_id import SkillId
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime

from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from shell.domain.user.value_objects.user_id import UserId
    from shell.platform.domain.value_objects.created_at import CreatedAt
    from shell.platform.domain.value_objects.deleted_at import DeletedAt


class UserSkill(AggregateRoot[SkillId]):
    __slots__ = (
        "_user_id",
        "_skill_data",
        "_created_at",
        "_updated_at",
        "_deleted_at",
    )

    _user_id: UserId
    _skill_data: SkillData

    def __init__(
        self,
        *,
        id: SkillId,
        user_id: UserId,
        skill_data: SkillData,
        created_at: CreatedAt | None = None,
        updated_at: UpdatedAt | None = None,
        deleted_at: DeletedAt | None = None,
    ) -> None:
        super().__init__(id)
        self._user_id = user_id
        self._skill_data = skill_data
        self._created_at = created_at
        self._updated_at = updated_at
        self._deleted_at = deleted_at

    @classmethod
    def restore(
        cls,
        *,
        id: SkillId,
        user_id: UserId,
        skill_data: SkillData,
        created_at: CreatedAt | None = None,
        updated_at: UpdatedAt | None = None,
        deleted_at: DeletedAt | None = None,
    ) -> Self:
        return cls(
            id=id,
            user_id=user_id,
            skill_data=skill_data,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
        )

    @classmethod
    def _new(cls, user_id: UserId, skill_data: JsonStr, now: CreatedAt) -> UserSkill:
        instance = cls(
            id=SkillId.generate(),
            user_id=user_id,
            skill_data=SkillData(skill_data),
            created_at=now,

        )
        instance.append_event(
            UserSkillCreatedEvent.now(
                skill_id=instance.id,
                user_id=user_id,
                now=now,
            )
        )
        return instance

    @classmethod
    def new(cls, user_id: UserId, skill_data: JsonStr, now: CreatedAt) -> UserSkill:
        return cls._new(user_id=user_id, skill_data=skill_data, now=now)


    def _delete(self) -> None:
        raise NotImplementedError("_delete() not yet implemented")


    def _update(self) -> None:
        raise NotImplementedError("_update() not yet implemented")

    @property
    def user_id(self) -> UserId:
        return self._user_id

    @property
    def skill_data(self) -> SkillData:
        return self._skill_data

    @property
    def created_at(self) -> CreatedAt | None:
        return self._created_at

    @property
    def updated_at(self) -> UpdatedAt | None:
        return self._updated_at

    @property
    def deleted_at(self) -> DeletedAt | None:
        return self._deleted_at
