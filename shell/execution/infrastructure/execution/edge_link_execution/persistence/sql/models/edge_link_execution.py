from __future__ import annotations

from datetime import datetime  # noqa: TC003 -- SQLAlchemy model uses datetime for column definition

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from shell.execution.infrastructure.execution.persistence.sql.models.base import (
    ExecutionSqlAlchemyModelBase,
)
from shell.platform.infrastructure.persistence.sql.models.mixins import VersionedMixin


class EdgeLinkExecutionModel(ExecutionSqlAlchemyModelBase, VersionedMixin):
    __tablename__ = "edge_link_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    node_execution_id: Mapped[str] = mapped_column(
        ForeignKey("node_execution.id", ondelete="CASCADE"),
        nullable=False,
    )
    edge_execution_id: Mapped[str] = mapped_column(
        ForeignKey("edge_execution.id", ondelete="CASCADE"),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)

    @declared_attr  # type: ignore[arg-type]
    def __mapper_args__(cls) -> dict[str, object]:
        return {"version_id_col": cls.version}
