from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.exceptions.domain_error import DomainError
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.domain.value_objects.updated_at import NONE_UPDATED_AT, UpdatedAt
from shell.project.domain.project.aggregates.project.events.project_created_event import (
    ProjectCreatedEvent,
)
from shell.project.domain.project.aggregates.project.events.project_deleted_event import (
    ProjectDeletedEvent,
)
from shell.project.domain.project.aggregates.project.events.project_updated_event import (
    ProjectUpdatedEvent,
)
from shell.project.domain.project.aggregates.project.value_objects.project_id import ProjectId
from shell.project.domain.project.aggregates.project.value_objects.project_status import (
    ProjectStatus,
)

if TYPE_CHECKING:
    from shell.project.domain.project.aggregates.project.value_objects.project_name import (
        ProjectName,
    )
    from shell.project.domain.project.aggregates.project.value_objects.repo_url import RepoUrl


class Project(AggregateRoot[ProjectId]):
    __slots__ = (
        "_created_at",
        "_updated_at",
        "_deleted_at",
        "_name",
        "_repo_url",
        "_status",
    )

    _name: ProjectName
    _repo_url: RepoUrl
    _status: ProjectStatus

    def __init__(
        self,
        *,
        id: ProjectId,
        created_at: CreatedAt,
        updated_at: UpdatedAt = NONE_UPDATED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        name: ProjectName,
        repo_url: RepoUrl,
        status: ProjectStatus,
    ) -> None:
        super().__init__(id)
        self._name = name
        self._repo_url = repo_url
        self._status = status
        self._created_at = created_at
        self._updated_at = updated_at
        self._deleted_at = deleted_at

    @classmethod
    def restore(
        cls,
        *,
        id: ProjectId,
        created_at: CreatedAt,
        updated_at: UpdatedAt = NONE_UPDATED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        name: ProjectName,
        repo_url: RepoUrl,
        status: ProjectStatus,
    ) -> Self:
        return cls(
            id=id,
            name=name,
            repo_url=repo_url,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
        )

    @classmethod
    def _new(
        cls,
        *,
        id_: ProjectId,
        now: OccurredAt,
        name: ProjectName,
        repo_url: RepoUrl,
    ) -> Project:
        instance = cls(
            id=id_,
            name=name,
            repo_url=repo_url,
            status=ProjectStatus.ACTIVE,
            created_at=CreatedAt.from_datetime(now.value),
        )
        instance.append_event(
            ProjectCreatedEvent.now(project_id=instance.id, now=OccurredAt.from_datetime(now.value))
        )
        return instance

    @classmethod
    def create(
        cls,
        *,
        id_: ProjectId,
        now: CreatedAt,
        name: ProjectName,
        repo_url: RepoUrl,
    ) -> Project:
        return cls._new(
            id_=id_, name=name, repo_url=repo_url, now=OccurredAt.from_datetime(now.value)
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            ProjectDeletedEvent.now(
                project_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            ProjectUpdatedEvent.now(
                project_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    @property
    def name(self) -> ProjectName:
        return self._name

    @property
    def repository_url(self) -> RepoUrl:
        return self._repo_url

    @property
    def status(self) -> ProjectStatus:
        return self._status

    @property
    def repo_url(self) -> RepoUrl:
        return self._repo_url

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def updated_at(self) -> UpdatedAt:
        return self._updated_at

    @property
    def deleted_at(self) -> DeletedAt:
        return self._deleted_at

    def update(self, *, name: ProjectName, repo_url: RepoUrl, now: UpdatedAt) -> None:
        """Update project fields and bump updated_at."""
        if self._deleted_at.value is not None:
            raise DomainError("Cannot update a deleted project")
        self._name = name
        self._repo_url = repo_url
        self._updated_at = now
        self.append_event(
            ProjectUpdatedEvent.now(
                project_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def delete(self, now: DeletedAt) -> None:
        """Soft-delete this project."""
        if self._deleted_at.value is not None:
            raise DomainError("Project already deleted")
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            ProjectDeletedEvent.now(
                project_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )
