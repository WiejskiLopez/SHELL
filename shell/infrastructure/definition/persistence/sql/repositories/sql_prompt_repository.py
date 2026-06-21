from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.repositories.prompt_repository import PromptRepository
from shell.domain.definition.value_objects.ids import (
    PromptId,  # noqa: TC002 — PromptId używany w konstruktorach w repozytorium
)
from shell.infrastructure.platform.persistence.sql.mappers import (
    prompt_entity_to_model,
    prompt_model_to_entity,
)
from sqlalchemy import select

from ..models import PromptModel

if TYPE_CHECKING:
    from shell.domain.definition.entities.prompt import Prompt
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlPromptRepository(PromptRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, prompt_id: PromptId) -> Prompt | None:
        query = select(PromptModel).where(PromptModel.id == prompt_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return prompt_model_to_entity(row) if row else None

    async def get_current_by_name(self, name: str) -> Prompt | None:
        query = select(PromptModel).where(PromptModel.name == name, PromptModel.is_current.is_(True))
        row = (await self._session.execute(query)).scalar_one_or_none()
        return prompt_model_to_entity(row) if row else None

    async def save(self, prompt: Prompt) -> None:
        model = prompt_entity_to_model(prompt)
        await self._session.merge(model)
