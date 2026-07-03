from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from shell.infrastructure.platform.persistence.sql.models.base import Base
from shell.infrastructure.platform.persistence.sql.models.mixins import VersionedMixin

if TYPE_CHECKING:
    from shell.infrastructure.execution.persistence.sql.models.graph_execution import (
        GraphExecutionModel,
    )
    from shell.infrastructure.execution.persistence.sql.models.graph_node_execution import (
        GraphNodeExecutionModel,
    )


class GraphNodeLinkExecutionModel(Base, VersionedMixin):
    __tablename__ = "graph_node_link_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    graph_execution_id: Mapped[str] = mapped_column(
        ForeignKey("graph_execution.id", ondelete="CASCADE"),
        nullable=False,
    )
    graph_node_execution_id: Mapped[str] = mapped_column(
        ForeignKey("graph_node_execution.id", ondelete="CASCADE"),
        nullable=False,
    )

    @declared_attr
    def __mapper_args__(cls) -> dict[str, Any]:
        return {"version_id_col": cls.version}

    graph_execution_model: Mapped[GraphExecutionModel] = relationship(
        "GraphExecutionModel",
    )

    graph_node_execution_model: Mapped[GraphNodeExecutionModel] = relationship(
        "GraphNodeExecutionModel",
    )
