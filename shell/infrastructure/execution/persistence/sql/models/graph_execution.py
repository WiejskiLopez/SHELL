from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shell.infrastructure.platform.persistence.sql.models._compat import JSONB
from shell.infrastructure.platform.persistence.sql.models.base import Base


class GraphExecutionModel(Base):
    __tablename__ = "graph_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    task_execution_id: Mapped[str] = mapped_column(
        ForeignKey("task_execution.id", ondelete="CASCADE"),
        nullable=False,
    )
    graph_definition_id: Mapped[str] = mapped_column(nullable=False, default="")
    status: Mapped[str] = mapped_column(nullable=False, default="CREATED")

    parent_graph_execution_id: Mapped[str | None] = mapped_column(
        ForeignKey("graph_execution.id", ondelete="SET NULL"),
        nullable=True,
    )
    state_input: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    state_output: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    depth: Mapped[int] = mapped_column(nullable=False, default=0)
    timeout_at: Mapped[datetime | None] = mapped_column(nullable=True)
    correlation_id: Mapped[str] = mapped_column(nullable=False, default="")
    tags: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    graph_node_execution_models: Mapped[list[GraphNodeExecutionModel]] = relationship(
        "GraphNodeExecutionModel",
        back_populates="graph_execution_model",
    )

    graph_node_transition_execution_models: Mapped[list[GraphNodeTransitionExecutionModel]] = relationship(
        "GraphNodeTransitionExecutionModel",
        back_populates="graph_execution_model",
        cascade="all, delete-orphan",
    )


from shell.infrastructure.execution.persistence.sql.models.graph_node_execution import GraphNodeExecutionModel
from shell.infrastructure.execution.persistence.sql.models.graph_node_transition_execution import GraphNodeTransitionExecutionModel
