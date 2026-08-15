from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.ingestion_service.application.ingestion.ingestion.dto.ingestion import IngestionDto
from shell.ingestion_service.infrastructure.ingestion.persistence.sql.models.ingestion import (
    IngestionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class IngestionQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, ingestion_id: str) -> IngestionDto | None:
        async with self._session_factory() as session:
            stmt = select(IngestionModel).where(IngestionModel.id == ingestion_id)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return IngestionDto(
                id=model.id,
                ingestion_data=model.ingestion_data,
                ingestion_context=model.ingestion_context,
                created_at=model.created_at,
                changed_at=model.changed_at,
                deleted_at=model.deleted_at,
            )


__all__ = [
    "IngestionQueryService",
]
