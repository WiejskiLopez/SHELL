from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] wymaga datetime w runtime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shell.infrastructure.platform.persistence.sql.models.base import Base

if TYPE_CHECKING:
    from shell.infrastructure.definition.persistence.sql.models.graph_definition import (  # noqa: E402 — łamie circular import NodeTransitionDefinitionModel ↔ GraphDefinitionModel
        GraphDefinitionModel,  # noqa: TC002 — GraphDefinitionModel używany w Mapped[GraphDefinitionModel] w relacji SQLAlchemy
    )


class NodeTransitionDefinitionModel(Base):
    __tablename__ = "node_transition_definition"

    id: Mapped[str] = mapped_column(primary_key=True)
    graph_definition_id: Mapped[str] = mapped_column(
        ForeignKey("graph_definition.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_node_definition_id: Mapped[str | None] = mapped_column(
        ForeignKey("node_definition.id", ondelete="SET NULL"),
        nullable=True,
    )
    target_node_definition_id: Mapped[str] = mapped_column(
        ForeignKey("node_definition.id", ondelete="CASCADE"),
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
        back_populates="node_transition_definition_models",
    )
