from __future__ import annotations

from datetime import datetime  # noqa: TC003 -- Mapped[datetime] requires datetime at runtime

from sqlalchemy.orm import Mapped, mapped_column

from shell.ingestion_service.infrastructure.ingestion.persistence.sql.models.base import (
    IngestionSqlAlchemyModelBase,
)
from shell.platform.infrastructure.persistence.sql.models.json_str_type import JsonStrType
from shell.platform.types import JsonStr


class IngestionModel(IngestionSqlAlchemyModelBase):
    __tablename__ = "ingestion"

    id: Mapped[str] = mapped_column(primary_key=True)
    ingestion_data: Mapped[JsonStr] = mapped_column(
        JsonStrType, nullable=False, default=lambda: JsonStr("{}")
    )
    ingestion_context: Mapped[JsonStr] = mapped_column(
        JsonStrType, nullable=False, default=lambda: JsonStr("{}")
    )
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
