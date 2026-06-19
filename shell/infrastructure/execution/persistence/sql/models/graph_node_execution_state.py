from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shell.infrastructure.platform.persistence.sql.models.base import Base


class GraphNodeExecutionStateModel(Base):
    __tablename__ = "node_state"

    id: Mapped[str] = mapped_column(primary_key=True)
    workflow_id: Mapped[str] = mapped_column(
        ForeignKey("workflow.id", ondelete="CASCADE"), nullable=False, index=True
    )
    graph_node_execution_id: Mapped[str] = mapped_column("graph_execution_id", nullable=False)
    status: Mapped[str] = mapped_column(nullable=False, default="idle")
    step: Mapped[int] = mapped_column(nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)

    workflow_model: Mapped[WorkflowModel] = relationship(
        "WorkflowModel", back_populates="graph_node_execution_state_models"
    )


from shell.infrastructure.execution.persistence.sql.models.workflow import WorkflowModel
