from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] wymaga datetime w runtime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from shell.execution.infrastructure.execution.persistence.sql.models.base import (
    ExecutionSqlAlchemyModelBase,
)


class NodeExecutionResultModel(ExecutionSqlAlchemyModelBase):
    __tablename__ = "node_execution_result"

    id: Mapped[str] = mapped_column(primary_key=True)
    node_execution_id: Mapped[str] = mapped_column(nullable=False)
    workflow_id: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    stdout: Mapped[str] = mapped_column(nullable=False, default="")
    stderr: Mapped[str] = mapped_column(nullable=False, default="")
    artifact_uri: Mapped[str] = mapped_column(nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(nullable=False)
