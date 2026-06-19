from __future__ import annotations

from sqlalchemy import ForeignKey

from shell.infrastructure.platform.persistence.sql.models._compat import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shell.infrastructure.platform.persistence.sql.models.base import Base


class GraphNodeExecutionModel(Base):
    __tablename__ = "graph_node_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    graph_execution_id: Mapped[str] = mapped_column(
        ForeignKey("graph_execution.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(nullable=False, default=0)
    mode: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(nullable=False, default="")
    node_type: Mapped[str] = mapped_column(nullable=False, default="")
    model: Mapped[str] = mapped_column(nullable=False, default="")
    command: Mapped[str] = mapped_column(nullable=False, default="")
    timeout: Mapped[int] = mapped_column(nullable=False, default=0)
    retries: Mapped[int] = mapped_column(nullable=False, default=0)
    log_level: Mapped[str] = mapped_column(nullable=False, default="INFO")
    max_step: Mapped[int] = mapped_column(nullable=False, default=0)
    no_ask_user: Mapped[bool] = mapped_column(nullable=False, default=False)
    autopilot: Mapped[bool] = mapped_column(nullable=False, default=False)
    task_execution_id: Mapped[str] = mapped_column(nullable=False, default="")
    source_dir: Mapped[str] = mapped_column(nullable=False, default="")
    status_initial: Mapped[str] = mapped_column(nullable=False, default="")
    sub_graph_definition_id: Mapped[str | None] = mapped_column(nullable=True)
    sub_graph_definition_version: Mapped[int | None] = mapped_column(nullable=True)
    timeout_seconds: Mapped[int] = mapped_column(nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(nullable=False, default=0)
    retry_delay_seconds: Mapped[int] = mapped_column(nullable=False, default=0)
    extra: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    graph_execution_model: Mapped[GraphExecutionModel] = relationship(
        "GraphExecutionModel", back_populates="graph_node_execution_models"
    )


from shell.infrastructure.execution.persistence.sql.models.graph_execution import GraphExecutionModel
