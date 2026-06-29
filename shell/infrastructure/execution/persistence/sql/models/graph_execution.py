from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] wymaga datetime w runtime

from shell.infrastructure.platform.persistence.sql.models._compat import JSONB
from shell.infrastructure.platform.persistence.sql.models.base import Base
from shell.infrastructure.platform.persistence.sql.models.mixins import VersionedMixin
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship


class GraphExecutionModel(Base, VersionedMixin):
    __tablename__ = "graph_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    task_execution_id: Mapped[str] = mapped_column(
        ForeignKey("task_execution.id", ondelete="CASCADE"),
        nullable=False,
    )
    graph_definition_id: Mapped[str] = mapped_column(nullable=False, default="")
    graph_node_definition_executions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    initialization_status: Mapped[str] = mapped_column(nullable=False, default="pending")
    status: Mapped[str] = mapped_column(nullable=False, default="created")

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

    @declared_attr  # type: ignore[arg-type]
    def __mapper_args__(cls) -> dict:
        return {"version_id_col": cls.version}

    graph_node_execution_models: Mapped[list[GraphNodeExecutionModel]] = relationship(
        "GraphNodeExecutionModel",
        back_populates="graph_execution_model",
    )

    graph_node_transition_execution_models: Mapped[list[GraphNodeTransitionExecutionModel]] = (
        relationship(
            "GraphNodeTransitionExecutionModel",
            back_populates="graph_execution_model",
            cascade="all, delete-orphan",
        )
    )


from shell.infrastructure.execution.persistence.sql.models.graph_node_execution import (  # noqa: E402 — łamie circular import GraphExecutionModel ↔ GraphNodeExecutionModel
    GraphNodeExecutionModel,  # noqa: TC002 — GraphNodeExecutionModel używany w Mapped[list[GraphNodeExecutionModel]] w relacji SQLAlchemy
)
from shell.infrastructure.execution.persistence.sql.models.graph_node_transition_execution import (  # noqa: E402 — łamie circular import GraphExecutionModel ↔ GraphNodeTransitionExecutionModel
    GraphNodeTransitionExecutionModel,  # noqa: TC002 — GraphNodeTransitionExecutionModel używany w Mapped[list[...]] w relacji SQLAlchemy
)
