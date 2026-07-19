from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.project.aggregates.project_skill.events.project_skill_created_event import (
    ProjectSkillCreatedEvent,
)
from shell.domain.project.aggregates.project_skill.events.project_skill_deleted_event import (
    ProjectSkillDeletedEvent,
)
from shell.domain.project.aggregates.project_skill.events.project_skill_updated_event import (
    ProjectSkillUpdatedEvent,
)
from shell.domain.project.aggregates.project_skill.value_objects.project_skill_data import (
    ProjectSkillData,
)
from shell.domain.project.aggregates.project_skill.value_objects.project_skill_id import (
    ProjectSkillId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime

if TYPE_CHECKING:
    from shell.domain.project.aggregates.project.value_objects.project_id import ProjectId


class ProjectSkill(AggregateRoot[ProjectSkillId]):
    __slots__ = (
        "_created_at",
        "_updated_at",
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
        updated_at: UpdatedAt | None = None,
        deleted_at: DeletedAt | None = None,
        project_id: ProjectId,
        skill_data: ProjectSkillData,
    ) -> None:
        super().__init__(id)
        self._project_id = project_id
        self._skill_data = skill_data
        self._created_at = created_at
        self._updated_at = UpdatedAt(value=None) if updated_at is None else updated_at
        self._deleted_at = DeletedAt(value=None) if deleted_at is None else deleted_at

    @classmethod
    def new(cls, project_id: ProjectId, skill_data: JsonStr, now: OccurredAt) -> ProjectSkill:
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

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            ProjectSkillDeletedEvent.now(
                project_skill_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            ProjectSkillUpdatedEvent.now(
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
    def created_at(self) -> CreatedAt | None:
        return self._created_at

    @property
    def updated_at(self) -> UpdatedAt:
        return self._updated_at

    @property
    def deleted_at(self) -> DeletedAt:
        return self._deleted_at

    @classmethod
    def restore(
        cls,
        *,
        id: ProjectSkillId,
        created_at: CreatedAt,
        updated_at: UpdatedAt | None = None,
        deleted_at: DeletedAt | None = None,
        project_id: ProjectId,
        skill_data: ProjectSkillData,
    ) -> Self:
        return cls(
            id=id,
            project_id=project_id,
            skill_data=skill_data,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
        )

    @classmethod
    def _new(cls, now: OccurredAt, project_id: ProjectId, skill_data: JsonStr) -> ProjectSkill:
        return cls.new(project_id=project_id, skill_data=skill_data, now=now)
