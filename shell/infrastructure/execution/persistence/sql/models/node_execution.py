from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from shell.infrastructure.platform.persistence.sql.models.base import Base
from shell.infrastructure.platform.persistence.sql.models.mixins import VersionedMixin


class NodeExecutionModel(Base, VersionedMixin):
    __tablename__ = "node_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    position: Mapped[int] = mapped_column(nullable=False, default=0)
    mode: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(nullable=False, default="")
    node_type: Mapped[str] = mapped_column(nullable=False, default="")
    model: Mapped[str] = mapped_column(nullable=False, default="")
    command: Mapped[str] = mapped_column(nullable=False, default="")
    retries: Mapped[int] = mapped_column(nullable=False, default=0)
    log_level: Mapped[str] = mapped_column(nullable=False, default="INFO")
    max_step: Mapped[int] = mapped_column(nullable=False, default=0)
    no_ask_user: Mapped[bool] = mapped_column(nullable=False, default=False)
    autopilot: Mapped[bool] = mapped_column(nullable=False, default=False)
    task_execution_id: Mapped[str] = mapped_column(nullable=False, default="")
    source_dir: Mapped[str] = mapped_column(nullable=False, default="")
    status: Mapped[str] = mapped_column(nullable=False, default="pending")
    status_initial: Mapped[str] = mapped_column(nullable=False, default="")

    @declared_attr  # type: ignore[arg-type]
    def __mapper_args__(cls) -> dict[str, Any]:
        return {"version_id_col": cls.version}
