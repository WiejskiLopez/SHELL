"""SQL ORM model <-> domain entity mappers for ProjectSkill aggregate."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shell.project_service.infrastructure.project.project_skill.persistence.sql.models.project_skill import (
    ProjectSkillModel,
)

if TYPE_CHECKING:
    from shell.project_service.domain.project.aggregates.project_skill.project_skill import (
        ProjectSkill,
    )


def project_skill_entity_to_model(entity: ProjectSkill) -> ProjectSkillModel:
    return ProjectSkillModel(
        id=entity.id.value,
        project_id=entity.project_id.value,
        skill_data=json.dumps(json.loads(entity.skill_data.value.value)),
        created_at=entity.created_at.value if entity.created_at else None,
        updated_at=entity.updated_at.value,
        deleted_at=entity.deleted_at.value,
    )
