from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] wymaga datetime w runtime

from shell.infrastructure.platform.persistence.sql.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column


class PromptModel(Base):
    __tablename__ = "prompt"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    hash: Mapped[str] = mapped_column(nullable=False)
    body: Mapped[str] = mapped_column(nullable=False, default="")
    source_uri: Mapped[str] = mapped_column(nullable=False, default="")
    is_current: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
