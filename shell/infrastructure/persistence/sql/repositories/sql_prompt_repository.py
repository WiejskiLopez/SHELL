from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.repositories.prompt_repository import PromptRepository
from shell.domain.value_objects.ids import PromptId

from ..mappers import (
    prompt_entity_to_model,
    prompt_model_to_entity,
)
from ..models import PromptModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.entities.prompt import Prompt


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
