from __future__ import annotations

from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class GraphNodeExecutionModel(Base):
    __tablename__ = "graph_node_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    graph_execution_id: Mapped[str] = mapped_column(
        ForeignKey("graph_execution.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(nullable=False, default=0)
    node_dir: Mapped[str] = mapped_column(nullable=False, default="")
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
    work_dir: Mapped[str] = mapped_column(nullable=False, default="")
    status_initial: Mapped[str] = mapped_column(nullable=False, default="")
    extra: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    graph_execution_model: Mapped[GraphExecutionModel] = relationship(
        "GraphExecutionModel", back_populates="graph_node_execution_models"
    )


from .graph_execution import GraphExecutionModel
