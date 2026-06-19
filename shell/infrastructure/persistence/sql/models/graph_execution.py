from __future__ import annotations

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class GraphExecutionModel(Base):
    __tablename__ = "graph_execution"
    __table_args__ = (Index("uq_graph_execution_task_execution_id", "task_execution_id", unique=True),)

    id: Mapped[str] = mapped_column(primary_key=True)
    task_execution_id: Mapped[str] = mapped_column(
        ForeignKey("task_execution.id", ondelete="CASCADE"),
        nullable=False,
    )
    graph_definition_id: Mapped[str] = mapped_column(nullable=False, default="")
    status: Mapped[str] = mapped_column(nullable=False, default="CREATED")

    graph_node_execution_models: Mapped[list[GraphNodeExecutionModel]] = relationship(
        "GraphNodeExecutionModel",
        back_populates="graph_execution_model",
        cascade="all, delete-orphan",
    )

    graph_node_transition_execution_models: Mapped[list[GraphNodeTransitionExecutionModel]] = relationship(
        "GraphNodeTransitionExecutionModel",
        back_populates="graph_execution_model",
        cascade="all, delete-orphan",
    )


from .graph_node_execution import GraphNodeExecutionModel
from .graph_node_transition_execution import GraphNodeTransitionExecutionModel
