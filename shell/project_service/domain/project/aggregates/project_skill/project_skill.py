from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.changed_at import NONE_CHANGED_AT, ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime
from shell.project_service.domain.project.aggregates.project_skill.events.project_skill_changed_event import (
    ProjectSkillChangedEvent,
)
from shell.project_service.domain.project.aggregates.project_skill.events.project_skill_created_event import (
    ProjectSkillCreatedEvent,
)
from shell.project_service.domain.project.aggregates.project_skill.events.project_skill_deleted_event import (
    ProjectSkillDeletedEvent,
)
from shell.project_service.domain.project.aggregates.project_skill.value_objects.project_skill_data import (
    ProjectSkillData,
)
from shell.project_service.domain.project.aggregates.project_skill.value_objects.project_skill_id import (
    ProjectSkillId,
)

if TYPE_CHECKING:
    from shell.project_service.domain.project.aggregates.project.value_objects.project_id import (
        ProjectId,
    )


class ProjectSkill(AggregateRoot[ProjectSkillId]):
    __slots__ = (
        "_created_at",
        "_changed_at",
        "_deleted_at",
        "_project_id",
        "_skill_data",
    )

    _project_id: ProjectId
    _skill_data: ProjectSkillData

    def __init__(
        self,
        *,
        id: ProjectSkillId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        project_id: ProjectId,
        skill_data: ProjectSkillData,
    ) -> None:
        super().__init__(id)
        self._project_id = project_id
        self._skill_data = skill_data
        self._created_at = created_at
        self._changed_at = changed_at
        self._deleted_at = deleted_at

    @classmethod
    def new(cls, project_id: ProjectId, skill_data: JsonStr, now: CreatedAt) -> ProjectSkill:
        return cls._new(
            project_id=project_id,
            skill_data=skill_data,
            now=OccurredAt.from_datetime(now.value),
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            ProjectSkillDeletedEvent.now(
                project_skill_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _change(self, now: OccurredAt) -> None:
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            ProjectSkillChangedEvent.now(
                project_skill_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    @property
    def project_id(self) -> ProjectId:
        return self._project_id

    @property
    def skill_data(self) -> ProjectSkillData:
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

    @classmethod
    def restore(
        cls,
        *,
        id: ProjectSkillId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        project_id: ProjectId,
        skill_data: ProjectSkillData,
    ) -> Self:
        return cls(
            id=id,
            project_id=project_id,
            skill_data=skill_data,
            created_at=created_at,
            changed_at=changed_at,
            deleted_at=deleted_at,
        )

    @classmethod
    def _new(cls, now: OccurredAt, project_id: ProjectId, skill_data: JsonStr) -> ProjectSkill:
        instance = cls(
            id=ProjectSkillId.generate(),
            project_id=project_id,
            skill_data=ProjectSkillData(skill_data),
            created_at=CreatedAt.from_datetime(now.value),
        )
        instance.append_event(
            ProjectSkillCreatedEvent.now(
                skill_id=instance.id,
                project_id=project_id,
                now=OccurredAt.from_datetime(now.value),
            )
        )
        return instance
