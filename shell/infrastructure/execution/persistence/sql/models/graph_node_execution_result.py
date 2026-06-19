from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from shell.infrastructure.platform.persistence.sql.models.base import Base


class GraphNodeExecutionResultModel(Base):
    __tablename__ = "graph_node_execution_result"

    id: Mapped[str] = mapped_column(primary_key=True)
    graph_node_execution_id: Mapped[str] = mapped_column(nullable=False, index=True)
    workflow_id: Mapped[str] = mapped_column(nullable=False, index=True)
    status: Mapped[str] = mapped_column(nullable=False)
    stdout: Mapped[str] = mapped_column(nullable=False, default="")
    stderr: Mapped[str] = mapped_column(nullable=False, default="")
    artifact_uri: Mapped[str] = mapped_column(nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(nullable=False)
