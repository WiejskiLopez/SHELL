from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey

from shell.infrastructure.platform.persistence.sql.models._compat import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shell.infrastructure.platform.persistence.sql.models.base import Base


class GraphNodeExecutionInputPayloadModel(Base):
    __tablename__ = "graph_node_execution_input_payload"

    id: Mapped[str] = mapped_column(primary_key=True)
    graph_node_execution_id: Mapped[str] = mapped_column(
        ForeignKey("graph_node_execution.id", ondelete="CASCADE"),
        nullable=False,
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_current: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    graph_node_execution_model: Mapped[GraphNodeExecutionModel] = relationship(
        "GraphNodeExecutionModel", back_populates="input_payload_models"
    )


from shell.infrastructure.execution.persistence.sql.models.graph_node_execution import (
    GraphNodeExecutionModel,
)
