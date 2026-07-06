from __future__ import annotations

from datetime import datetime  # noqa: TC003 -- SQLAlchemy model uses datetime for column definition
from typing import Any

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from shell.infrastructure.platform.persistence.sql.models.base import Base
from shell.infrastructure.platform.persistence.sql.models.mixins import VersionedMixin


class EdgeExecutionModel(Base, VersionedMixin):
    __tablename__ = "edge_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    edge_definition_id: Mapped[str] = mapped_column(nullable=False, default="")
    source_node_execution_id: Mapped[str] = mapped_column(nullable=False)
    target_node_execution_id: Mapped[str | None] = mapped_column(
        ForeignKey("node_execution.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)

    @declared_attr  # type: ignore[arg-type]
    def __mapper_args__(cls) -> dict[str, Any]:
        return {"version_id_col": cls.version}
