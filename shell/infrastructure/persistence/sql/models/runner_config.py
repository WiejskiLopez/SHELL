from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class RunnerConfigModel(Base):
    __tablename__ = "runner_config"

    id: Mapped[str] = mapped_column(primary_key=True)
    package_name: Mapped[str] = mapped_column(nullable=False, index=True)
    kind: Mapped[str] = mapped_column(nullable=False)
    hash: Mapped[str] = mapped_column(nullable=False)
    body: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
