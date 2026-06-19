from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.application.dto import PromptDto
from shell.infrastructure.persistence.sql.models import PromptModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class PromptQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_prompt(self, name: str) -> PromptDto | None:
        async with self._session_factory() as session:
            stmt = select(PromptModel).where(PromptModel.name == name)
            res = await session.execute(stmt)
            prompt_model = res.scalar_one_or_none()
            if not prompt_model:
                return None
            return PromptDto(
                id=prompt_model.id,
                name=prompt_model.name,
                body=prompt_model.body,
                version=prompt_model.version,
                hash=prompt_model.hash,
                is_current=prompt_model.is_current,
                created_at=prompt_model.created_at,
            )
