from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from shell.domain.platform.base.entity import Entity
from shell.domain.projekt.value_objects.project_id import ProjectId

if TYPE_CHECKING:
    from datetime import datetime


class ProjectSkill(Entity[str]):
    __slots__ = ("_project_id", "_payload", "_created_at")

    def __init__(
        self,
        id: str,
        project_id: ProjectId,
        payload: dict[str, Any],
        created_at: datetime,
    ) -> None:
        super().__init__(id)
        self._project_id = project_id
        self._payload = payload
        self._created_at = created_at

    @property
    def project_id(self) -> ProjectId:
        return self._project_id

    @property
    def payload(self) -> dict[str, Any]:
        return self._payload

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @classmethod
    def new(cls, project_id: ProjectId, payload: dict[str, Any], now: datetime) -> ProjectSkill:
        return cls(id=str(uuid.uuid4()), project_id=project_id, payload=payload, created_at=now)
