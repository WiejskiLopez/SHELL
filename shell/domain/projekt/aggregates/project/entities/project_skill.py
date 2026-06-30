from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.platform.base.entity import Entity
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.projekt.value_objects.project_skill_id import ProjectSkillId
from shell.domain.projekt.value_objects.project_skill_payload import ProjectSkillPayload

if TYPE_CHECKING:
    from shell.domain.projekt.value_objects.project_id import ProjectId


class ProjectSkill(Entity[ProjectSkillId]):
    __slots__ = ("_project_id", "_payload", "_created_at")

    _project_id: ProjectId
    _payload: ProjectSkillPayload
    _created_at: CreatedAt

    def __init__(
        self,
        id: ProjectSkillId,
        project_id: ProjectId,
        payload: ProjectSkillPayload,
        created_at: CreatedAt | None = None,
    ) -> None:
        super().__init__(id)
        self._project_id = project_id
        self._payload = payload
        self._created_at = created_at or CreatedAt.now()

    @property
    def project_id(self) -> ProjectId:
        return self._project_id

    @property
    def payload(self) -> ProjectSkillPayload:
        return self._payload

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @classmethod
    def new(
        cls, project_id: ProjectId, payload: dict[str, Any], now: CreatedAt | None = None
    ) -> ProjectSkill:
        return cls(
            id=ProjectSkillId.generate(),
            project_id=project_id,
            payload=ProjectSkillPayload(payload),
            created_at=now,
        )
