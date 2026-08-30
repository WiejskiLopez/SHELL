from __future__ import annotations

from datetime import datetime  # noqa: TC003 - SQLAlchemy resolves Mapped[...] at class definition

from sqlalchemy import String
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from shell.execution_service.infrastructure.execution.persistence.sql.models.base import (
    ExecutionSqlAlchemyModelBase,
)
from shell.platform.infrastructure.persistence.sql.models.mixins import VersionedMixin


class NodeExecutionModel(ExecutionSqlAlchemyModelBase, VersionedMixin):
    __tablename__ = "node_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    position: Mapped[int] = mapped_column(nullable=False, default=0)
    node_type: Mapped[str] = mapped_column(nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    model: Mapped[str] = mapped_column(nullable=False, default="")
    command: Mapped[str] = mapped_column(nullable=False, default="")
    retries: Mapped[int] = mapped_column(nullable=False, default=0)
    log_level: Mapped[str] = mapped_column(nullable=False, default="INFO")
    max_step: Mapped[int] = mapped_column(nullable=False, default=0)
    no_ask_user: Mapped[bool] = mapped_column(nullable=False, default=False)
    autopilot: Mapped[bool] = mapped_column(nullable=False, default=False)
    task_execution_id: Mapped[str] = mapped_column(nullable=False, default="")
    source_dir: Mapped[str] = mapped_column(nullable=False, default="")
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    status_initial: Mapped[str] = mapped_column(nullable=False, default="")

    @declared_attr  # type: ignore[arg-type]
    def __mapper_args__(cls) -> dict[str, object]:
        return {"version_id_col": cls.version}
