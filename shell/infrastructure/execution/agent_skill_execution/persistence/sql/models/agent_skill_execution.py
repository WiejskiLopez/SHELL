from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column

from shell.infrastructure.platform.persistence.sql.models._compat import JSONB
from shell.infrastructure.platform.persistence.sql.models.base import Base

if TYPE_CHECKING:
    from datetime import datetime



class AgentSkillExecutionModel(Base):
    __tablename__ = "agent_skill_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    agent_execution_id: Mapped[str] = mapped_column(nullable=False)
    skill_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
