from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.changed_at import NONE_CHANGED_AT, ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.user_service.domain.user.aggregates.user_skill.events.user_skill_changed_event import (
    UserSkillChangedEvent,
)
from shell.user_service.domain.user.aggregates.user_skill.events.user_skill_created_event import (
    UserSkillCreatedEvent,
)
from shell.user_service.domain.user.aggregates.user_skill.events.user_skill_deleted_event import (
    UserSkillDeletedEvent,
)
from shell.user_service.domain.user.aggregates.user_skill.value_objects.user_skill_id import (
    UserSkillId,
)
from shell.user_service.domain.user.value_objects.skill_data import SkillData

if TYPE_CHECKING:
    from shell.platform.types import JsonStr
    from shell.user_service.domain.user.value_objects.user_id import UserId


class UserSkill(AggregateRoot[UserSkillId]):
    __slots__ = (
        "_created_at",
        "_changed_at",
        "_deleted_at",
        "_user_id",
        "_skill_data",
    )

    _user_id: UserId
    _skill_data: SkillData

    def __init__(
        self,
        *,
        id: UserSkillId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        user_id: UserId,
        skill_data: SkillData,
    ) -> None:
        super().__init__(id)
        self._user_id = user_id
        self._skill_data = skill_data
        self._created_at = created_at
        self._changed_at = changed_at
        self._deleted_at = deleted_at

    @classmethod
    def restore(
        cls,
        *,
        id: UserSkillId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        user_id: UserId,
        skill_data: SkillData,
    ) -> Self:
        return cls(
            id=id,
            user_id=user_id,
            skill_data=skill_data,
            created_at=created_at,
            changed_at=changed_at,
            deleted_at=deleted_at,
        )

    @classmethod
    def _new(cls, now: OccurredAt, user_id: UserId, skill_data: JsonStr) -> UserSkill:
        instance = cls(
            id=UserSkillId.generate(),
            user_id=user_id,
            skill_data=SkillData(skill_data),
            created_at=CreatedAt.from_datetime(now.value),
        )
        instance.append_event(
            UserSkillCreatedEvent.now(
                skill_id=instance.id,
                user_id=user_id,
                now=OccurredAt.from_datetime(now.value),
            )
        )
        return instance

    @classmethod
    def new(cls, user_id: UserId, skill_data: JsonStr, now: CreatedAt) -> UserSkill:
        return cls._new(
            user_id=user_id, skill_data=skill_data, now=OccurredAt.from_datetime(now.value)
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            UserSkillDeletedEvent.now(
                user_skill_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _change(self, now: OccurredAt) -> None:
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            UserSkillChangedEvent.now(
                user_skill_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    @property
    def user_id(self) -> UserId:
        return self._user_id

    @property
    def skill_data(self) -> SkillData:
        return self._skill_data

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def changed_at(self) -> ChangedAt:
        return self._changed_at

    @property
    def deleted_at(self) -> DeletedAt:
        return self._deleted_at
