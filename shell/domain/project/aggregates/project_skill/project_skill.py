from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.project.aggregates.project_skill.events.project_skill_created_event import (
    ProjectSkillCreatedEvent,
)
from shell.domain.project.value_objects.project_skill_data import ProjectSkillData
from shell.domain.project.value_objects.project_skill_id import ProjectSkillId

if TYPE_CHECKING:
    from shell.domain.project.value_objects.project_id import ProjectId


from shell.domain.platform.value_objects.deleted_at import DeletedAt
from shell.domain.platform.value_objects.updated_at import UpdatedAt


class ProjectSkill(AggregateRoot[ProjectSkillId]):
    __slots__ = (
        "_project_id",
        "_skill_data",
        "_created_at",
        "_updated_at",
        "_deleted_at",
    )

    _project_id: ProjectId
    _skill_data: ProjectSkillData

    def __init__(
        self,
        *,
        id: ProjectSkillId,
        project_id: ProjectId,
        skill_data: ProjectSkillData,
        created_at: CreatedAt | None = None,
        updated_at: UpdatedAt | None = None,
        deleted_at: DeletedAt | None = None,
    ) -> None:
        super().__init__(id)
        self._project_id = project_id
        self._skill_data = skill_data
        self._created_at = created_at
        self._updated_at = updated_at
        self._deleted_at = deleted_at

    @classmethod
    def restore(
        cls,
        *,
        id: ProjectSkillId,
        project_id: ProjectId,
        skill_data: ProjectSkillData,
        created_at: CreatedAt | None = None,
        updated_at: UpdatedAt | None = None,
        deleted_at: DeletedAt | None = None,
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
    def new(
        cls, project_id: ProjectId, skill_data: dict[str, Any], now: CreatedAt | None = None
    ) -> ProjectSkill:
        actual_now = now or CreatedAt.now()
        instance = cls(
            id=ProjectSkillId.generate(),
            project_id=project_id,
            skill_data=ProjectSkillData(skill_data),
            created_at=actual_now,
        )
        instance.append_event(
            ProjectSkillCreatedEvent.now(
                skill_id=instance.id,
                project_id=project_id,
                now=actual_now,
            )
        )
        return instance

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
    def updated_at(self) -> UpdatedAt | None:
        return self._updated_at

    @property
    def deleted_at(self) -> DeletedAt | None:
        return self._deleted_at
