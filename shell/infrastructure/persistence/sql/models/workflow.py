from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class WorkflowModel(Base):
    __tablename__ = "workflow"

    id: Mapped[str] = mapped_column(primary_key=True)
    task_execution_id: Mapped[str] = mapped_column(nullable=False, index=True)
    status: Mapped[str] = mapped_column(nullable=False, default="idle")
    current_graph_node_execution_id: Mapped[str | None] = mapped_column(
        nullable=True, default=None, index=True
    )
    work_dir: Mapped[str] = mapped_column(nullable=False, default="")
    correlation_id: Mapped[str] = mapped_column(nullable=False, default="")
    version: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    graph_node_execution_state_models: Mapped[list[GraphNodeExecutionStateModel]] = relationship(
        "GraphNodeExecutionStateModel",
        back_populates="workflow_model",
        cascade="all, delete-orphan",
    )

    graph_node_execution_result_models: Mapped[list[GraphNodeExecutionResultModel]] = relationship(
        "GraphNodeExecutionResultModel",
        primaryjoin="WorkflowModel.id == foreign(GraphNodeExecutionResultModel.workflow_id)",
        cascade="all, delete-orphan",
    )


from .graph_node_execution_state import GraphNodeExecutionStateModel
from .graph_node_execution_result import GraphNodeExecutionResultModel
