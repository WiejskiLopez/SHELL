from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey

from ._compat import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class GraphExecutionStateModel(Base):
    __tablename__ = "graph_execution_state"

    id: Mapped[str] = mapped_column(primary_key=True)
    graph_execution_id: Mapped[str] = mapped_column(
        ForeignKey("graph_execution.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_current: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
