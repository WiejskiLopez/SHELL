from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship

from shell.infrastructure.platform.persistence.sql.models.base import Base


class WorkflowModel(Base):
    __tablename__ = "workflow"

    id: Mapped[str] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(nullable=False, default="idle")
    current_graph_node_execution_id: Mapped[str | None] = mapped_column(
        nullable=True, default=None
    )
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


from shell.infrastructure.execution.persistence.sql.models.graph_node_execution_state import GraphNodeExecutionStateModel
from shell.infrastructure.execution.persistence.sql.models.graph_node_execution_result import GraphNodeExecutionResultModel
