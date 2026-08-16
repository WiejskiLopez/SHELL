"""Development seed data for the Project bounded context.

Idempotent: records are inserted only when missing, so the seed can be
run repeatedly against the same database without creating duplicates.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.project_service.infrastructure.project.project.persistence.sql.models.project import (
    ProjectModel,
)
from shell.project_service.infrastructure.project.seed.builders import (
    build_project_model,
    build_project_skill_model,
    build_project_state_model,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

DEV_ID_PREFIX = "dev"

_PROJECTS_DATA: list[dict[str, str | None]] = [
    {
        "id": f"{DEV_ID_PREFIX}-project-alpha",
        "name": "Alpha",
        "repo_url": "https://github.com/example/alpha",
        "status": "active",
    },
    {
        "id": f"{DEV_ID_PREFIX}-project-beta",
        "name": "Beta",
        "repo_url": "https://github.com/example/beta",
        "status": "active",
    },
    {
        "id": f"{DEV_ID_PREFIX}-project-gamma",
        "name": "Gamma",
        "repo_url": None,
        "status": "archived",
    },
]


def seed_dev_sync(session: Session) -> None:
    """Insert dev projects with their states and skills when missing."""
    for project_data in _PROJECTS_DATA:
        project_id = str(project_data["id"])
        existing_project = session.execute(
            select(ProjectModel).where(ProjectModel.id == project_id)
        ).scalar_one_or_none()
        if existing_project is not None:
            continue

        project_name = str(project_data["name"])
        project_status = str(project_data["status"])
        session.add(
            build_project_model(
                project_id=project_id,
                name=project_name,
                repo_url=project_data["repo_url"],
                status=project_status,
            )
        )

        for direction in ("INPUT", "OUTPUT"):
            session.add(
                build_project_state_model(
                    state_id=f"{project_id}-state-{direction.lower()}",
                    project_id=project_id,
                    direction=direction,
                    state_data={"name": project_name, "phase": direction.lower()},
                )
            )

        skill_name = "python-dev" if project_status == "active" else "legacy-maintenance"
        skill_level = "expert" if project_status == "active" else "intermediate"
        session.add(
            build_project_skill_model(
                skill_id=f"{project_id}-skill-1",
                project_id=project_id,
                skill_data={"name": skill_name, "level": skill_level},
            )
        )


__all__ = ["DEV_ID_PREFIX", "seed_dev_sync"]
