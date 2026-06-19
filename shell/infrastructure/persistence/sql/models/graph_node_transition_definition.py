from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class GraphNodeTransitionDefinitionModel(Base):
    __tablename__ = "graph_node_transition_definition"

    id: Mapped[str] = mapped_column(primary_key=True)
    graph_definition_id: Mapped[str] = mapped_column(
        ForeignKey("graph_definition.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_node_definition_id: Mapped[str | None] = mapped_column(
        ForeignKey("graph_node_definition.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_node_definition_id: Mapped[str] = mapped_column(
        ForeignKey("graph_node_definition.id", ondelete="CASCADE"),
        nullable=False,
    )

    transition_type: Mapped[str] = mapped_column(nullable=False, default="sequence")
    priority: Mapped[int] = mapped_column(nullable=False, default=0)

    condition_expression: Mapped[str | None] = mapped_column(nullable=True)
    condition_language: Mapped[str | None] = mapped_column(nullable=True)

    join_wait_count: Mapped[int | None] = mapped_column(nullable=True)
    max_loop_count: Mapped[int] = mapped_column(nullable=False, default=0)
    timeout_seconds: Mapped[int | None] = mapped_column(nullable=True)
    retry_count: Mapped[int] = mapped_column(nullable=False, default=0)
    retry_delay_seconds: Mapped[int] = mapped_column(nullable=False, default=0)

    data_mapping: Mapped[dict | None] = mapped_column(sa.JSON, nullable=True)
    label: Mapped[str] = mapped_column(nullable=False, default="")

    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)

    graph_definition_model: Mapped[GraphDefinitionModel] = relationship(
        back_populates="graph_node_transition_definition_models",
    )


from .graph_definition import GraphDefinitionModel
