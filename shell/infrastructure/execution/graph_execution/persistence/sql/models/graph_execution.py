from __future__ import annotations

from datetime import (
    datetime,  # noqa: TC003 — needed by SQLAlchemy ORM at runtime for Mapped[datetime | None]
)
from typing import Any

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from shell.platform.infrastructure.persistence.sql.models._compat import JSONB
from shell.platform.infrastructure.persistence.sql.models.base import Base
from shell.platform.infrastructure.persistence.sql.models.mixins import VersionedMixin


class GraphExecutionModel(Base, VersionedMixin):
    __tablename__ = "graph_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    task_execution_id: Mapped[str] = mapped_column(
        ForeignKey("task_execution.id", ondelete="CASCADE"),
        nullable=False,
    )
    graph_definition_id: Mapped[str] = mapped_column(nullable=False, default="")
    status: Mapped[str] = mapped_column(nullable=False, default="created")

    parent_graph_execution_id: Mapped[str | None] = mapped_column(
        ForeignKey("graph_execution.id", ondelete="SET NULL"),
        nullable=True,
    )
    state_input: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    state_output: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    depth: Mapped[int] = mapped_column(nullable=False, default=0)
    max_subgraph_depth: Mapped[int] = mapped_column(nullable=False, default=5)
    timeout_at: Mapped[datetime | None] = mapped_column(nullable=True)
    correlation_id: Mapped[str] = mapped_column(nullable=False, default="")
    tags: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    updated_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)

    @declared_attr  # type: ignore[arg-type]
    def __mapper_args__(cls) -> dict[str, Any]:
        return {"version_id_col": cls.version}
