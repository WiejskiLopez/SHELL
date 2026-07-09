from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] wymaga datetime w runtime

from sqlalchemy.orm import Mapped, mapped_column

from shell.infrastructure.platform.persistence.sql.models.base import Base


class RunnerConfigModel(Base):
    __tablename__ = "runner_config"

    id: Mapped[str] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
