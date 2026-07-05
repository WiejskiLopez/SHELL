from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] requires datetime at runtime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from shell.infrastructure.platform.persistence.sql.models.base import Base
from shell.infrastructure.user.persistence.sql.models._compat import JSONB


class UserSkillModel(Base):
    __tablename__ = "user_skill"

    id: Mapped[str] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    updated_at: Mapped[datetime] = mapped_column(nullable=True)
