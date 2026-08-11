from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] wymaga datetime w runtime

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from shell.definition.infrastructure.definition.persistence.sql.models.base import (
    DefinitionSqlAlchemyModelBase,
)


class RunnerConfigModel(DefinitionSqlAlchemyModelBase):
    __tablename__ = "runner_config"

    id: Mapped[str] = mapped_column(primary_key=True)
    package_name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    hash: Mapped[str] = mapped_column(String(64), nullable=False)
    body: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    version: Mapped[int] = mapped_column(nullable=False, default=1)
