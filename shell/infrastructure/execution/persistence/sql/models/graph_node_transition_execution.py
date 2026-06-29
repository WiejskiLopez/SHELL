from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] wymaga datetime w runtime

import sqlalchemy as sa
from shell.infrastructure.platform.persistence.sql.models.base import Base
from shell.infrastructure.platform.persistence.sql.models.mixins import VersionedMixin
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship


class GraphNodeTransitionExecutionModel(Base, VersionedMixin):
    __tablename__ = "graph_node_transition_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    graph_execution_id: Mapped[str] = mapped_column(
        ForeignKey("graph_execution.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_node_execution_id: Mapped[str | None] = mapped_column(
        ForeignKey("graph_node_execution.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_node_execution_id: Mapped[str] = mapped_column(
        ForeignKey("graph_node_execution.id", ondelete="CASCADE"),
        nullable=False,
    )

    transition_type: Mapped[str] = mapped_column(nullable=False, default="sequence")
    priority: Mapped[int] = mapped_column(nullable=False, default=0)

    condition_expression: Mapped[str | None] = mapped_column(nullable=True)
    condition_language: Mapped[str | None] = mapped_column(nullable=True)

    join_wait_count: Mapped[int | None] = mapped_column(nullable=True)
    current_iteration: Mapped[int] = mapped_column(nullable=False, default=0)
    status: Mapped[str] = mapped_column(nullable=False, default="evaluated")
    max_loop_count: Mapped[int] = mapped_column(nullable=False, default=0)
    timeout_seconds: Mapped[int | None] = mapped_column(nullable=True)
    retry_count: Mapped[int] = mapped_column(nullable=False, default=0)
    retry_delay_seconds: Mapped[int] = mapped_column(nullable=False, default=0)

    data_mapping: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    label: Mapped[str] = mapped_column(nullable=False, default="")

    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)

    @declared_attr  # type: ignore[arg-type]
    def __mapper_args__(cls) -> dict:
        return {"version_id_col": cls.version}

    graph_execution_model: Mapped[GraphExecutionModel] = relationship(
        back_populates="graph_node_transition_execution_models",
    )


from shell.infrastructure.execution.persistence.sql.models.graph_execution import (  # noqa: E402 — łamie circular import GraphNodeTransitionExecutionModel ↔ GraphExecutionModel
    GraphExecutionModel,  # noqa: TC002 — GraphExecutionModel używany w Mapped[GraphExecutionModel] w relacji SQLAlchemy
)
