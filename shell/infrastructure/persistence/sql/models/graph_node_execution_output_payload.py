from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey

from ._compat import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class GraphNodeExecutionOutputPayloadModel(Base):
    __tablename__ = "graph_node_execution_output_payload"

    id: Mapped[str] = mapped_column(primary_key=True)
    graph_node_execution_id: Mapped[str] = mapped_column(
        ForeignKey("graph_node_execution.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_current: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
