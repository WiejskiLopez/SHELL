from __future__ import annotations

from datetime import datetime  # noqa: TC003 -- Mapped[datetime] requires datetime at runtime

from sqlalchemy.orm import Mapped, mapped_column

from shell.platform.infrastructure.persistence.sql.models.base import Base
from shell.platform.infrastructure.persistence.sql.models.json_str_type import JsonStrType
from shell.platform.types import JsonStr


class MessageRouterModel(Base):
    __tablename__ = "message_router"

    id: Mapped[str] = mapped_column(primary_key=True)
    message_data: Mapped[JsonStr] = mapped_column(
        JsonStrType, nullable=False, default=lambda: JsonStr("{}")
    )
    message_context: Mapped[JsonStr] = mapped_column(
        JsonStrType, nullable=False, default=lambda: JsonStr("{}")
    )
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
