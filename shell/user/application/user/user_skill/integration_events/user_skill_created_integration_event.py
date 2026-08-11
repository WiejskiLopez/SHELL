from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.events import IntegrationEvent


@dataclass(frozen=True, slots=True)
class UserSkillCreatedIntegrationEvent(IntegrationEvent):
    skill_id: str
    user_id: str
