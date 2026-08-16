from __future__ import annotations

from typing import TYPE_CHECKING, cast

from shell.project_service.infrastructure.project.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS,
)
from shell.project_service.infrastructure.project.project_skill.persistence.sql.unit_of_work import (
    SqlAlchemyProjectSkillUnitOfWork,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


def test_project_skill_unit_of_work_uses_project_delivery_models() -> None:
    session_factory = cast("async_sessionmaker[AsyncSession]", object())

    unit_of_work = SqlAlchemyProjectSkillUnitOfWork(session_factory)

    assert unit_of_work._models is PERSISTENCE_DELIVERY_MODELS
