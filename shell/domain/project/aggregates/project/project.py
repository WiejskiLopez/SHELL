from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.project.aggregates.project.value_objects.project_id import ProjectId
from shell.domain.project.aggregates.project.value_objects.project_status import ProjectStatus
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.project.aggregates.project.value_objects.project_name import ProjectName
    from shell.domain.project.aggregates.project.value_objects.repo_url import RepoUrl
    from shell.platform.domain.value_objects.created_at import CreatedAt


class Project(AggregateRoot[ProjectId]):
    __slots__ = (
        "_name",
        "_repo_url",
        "_status",
        "_created_at",
        "_updated_at",
        "_deleted_at",
    )

    _name: ProjectName
    _repo_url: RepoUrl
    _status: ProjectStatus

    def __init__(
        self,
        *,
        id: ProjectId,
        name: ProjectName,
        repo_url: RepoUrl,
        status: ProjectStatus = ProjectStatus.ACTIVE,
        created_at: CreatedAt | None = None,
        updated_at: UpdatedAt | None = None,
        deleted_at: DeletedAt | None = None,
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
        name: ProjectName,
        repo_url: RepoUrl,
        status: ProjectStatus = ProjectStatus.ACTIVE,
        created_at: CreatedAt | None = None,
        updated_at: UpdatedAt | None = None,
        deleted_at: DeletedAt | None = None,
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
    def created_at(self) -> CreatedAt | None:
        return self._created_at

    @property
    def updated_at(self) -> UpdatedAt | None:
        return self._updated_at

    @property
    def deleted_at(self) -> DeletedAt | None:
        return self._deleted_at

    def update(self, *, name: ProjectName, repo_url: RepoUrl, now: datetime) -> None:
        """Update project fields and bump updated_at."""
        self._name = name
        self._repo_url = repo_url
        self._updated_at = UpdatedAt.from_datetime(now)

    def delete(self, now: datetime) -> None:
        """Soft-delete this project."""
        self._deleted_at = DeletedAt.from_datetime(now)
        self._updated_at = UpdatedAt.from_datetime(now)
