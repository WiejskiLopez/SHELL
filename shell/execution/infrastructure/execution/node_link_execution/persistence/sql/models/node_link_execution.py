from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] requires datetime at runtime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from shell.platform.infrastructure.persistence.sql.models.base import Base
from shell.platform.infrastructure.persistence.sql.models.mixins import VersionedMixin

if TYPE_CHECKING:
    from shell.execution.infrastructure.execution.graph_execution.persistence.sql.models.graph_execution import (
        GraphExecutionModel,
    )
    from shell.execution.infrastructure.execution.node_execution.persistence.sql.models.node_execution import (
        NodeExecutionModel,
    )


class NodeLinkExecutionModel(Base, VersionedMixin):
    __tablename__ = "node_link_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    graph_execution_id: Mapped[str] = mapped_column(
        ForeignKey("graph_execution.id", ondelete="CASCADE"),
        nullable=False,
    )
    node_execution_id: Mapped[str] = mapped_column(
        ForeignKey("node_execution.id", ondelete="CASCADE"),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)

    @declared_attr  # type: ignore[arg-type]
    def __mapper_args__(cls) -> dict[str, object]:
        return {"version_id_col": cls.version}

    graph_execution_model: Mapped[GraphExecutionModel] = relationship(
        "GraphExecutionModel",
    )

    node_execution_model: Mapped[NodeExecutionModel] = relationship(
        "NodeExecutionModel",
    )
