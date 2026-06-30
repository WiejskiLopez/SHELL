from __future__ import annotations

from datetime import datetime  # noqa: TC003 -- Mapped[datetime] requires datetime at runtime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from shell.infrastructure.execution.persistence.sql.models._compat import JSONB
from shell.infrastructure.platform.persistence.sql.models.base import Base


class UserExecutionStateModel(Base):
    __tablename__ = "user_execution_state"

    id: Mapped[str] = mapped_column(primary_key=True)
    user_execution_id: Mapped[str] = mapped_column(
        ForeignKey("user_execution.id", ondelete="CASCADE"),
        nullable=False,
    )
    direction: Mapped[str] = mapped_column(nullable=False)
    state_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_current: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
