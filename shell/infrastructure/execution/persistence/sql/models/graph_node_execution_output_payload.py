from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] wymaga datetime w runtime

from shell.infrastructure.platform.persistence.sql.models._compat import JSONB
from shell.infrastructure.platform.persistence.sql.models.base import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


class GraphNodeExecutionOutputPayloadModel(Base):
    __tablename__ = "graph_node_execution_output_payload"

    id: Mapped[str] = mapped_column(primary_key=True)
    graph_node_execution_id: Mapped[str] = mapped_column(
        ForeignKey("graph_node_execution.id", ondelete="CASCADE"),
        nullable=False,
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_current: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    graph_node_execution_model: Mapped[GraphNodeExecutionModel] = relationship(
        "GraphNodeExecutionModel", back_populates="output_payload_models"
    )


from shell.infrastructure.execution.persistence.sql.models.graph_node_execution import (  # noqa: E402 — łamie circular import GraphNodeExecutionOutputPayloadModel ↔ GraphNodeExecutionModel
    GraphNodeExecutionModel,  # noqa: TC002 — GraphNodeExecutionModel używany w Mapped[GraphNodeExecutionModel] w relacji SQLAlchemy
)
