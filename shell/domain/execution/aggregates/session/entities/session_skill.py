from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.session.value_objects.session_id import SessionId
from shell.domain.execution.aggregates.session.value_objects.session_skill_id import SessionSkillId
from shell.domain.execution.value_objects.skill_payload import SkillPayload
from shell.domain.platform.base.entity import Entity

if TYPE_CHECKING:
    from datetime import datetime


class SessionSkill(Entity[SessionSkillId]):
    __slots__ = ("_session_id", "_payload", "_created_at")

    def __init__(
        self,
        id: SessionSkillId,
        session_id: SessionId,
        payload: SkillPayload,
        created_at: datetime,
    ) -> None:
        super().__init__(id)
        self._session_id = session_id
        self._payload = payload
        self._created_at = created_at

    @property
    def session_id(self) -> SessionId:
        return self._session_id

    @property
    def payload(self) -> SkillPayload:
        return self._payload

    @property
    def created_at(self) -> datetime:
        return self._created_at
