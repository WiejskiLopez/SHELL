from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectSkillGetByIdQuery:
    project_skill_id: str
