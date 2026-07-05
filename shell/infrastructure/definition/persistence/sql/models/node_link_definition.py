from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from shell.infrastructure.platform.persistence.sql.models.base import Base
from shell.infrastructure.platform.persistence.sql.models.mixins import VersionedMixin

if TYPE_CHECKING:
    from shell.infrastructure.definition.persistence.sql.models.graph_definition import (
        GraphDefinitionModel,
    )
    from shell.infrastructure.definition.persistence.sql.models.node_definition import (
        NodeDefinitionModel,
    )


class NodeLinkDefinitionModel(Base, VersionedMixin):
    __tablename__ = "node_link_definition"

    id: Mapped[str] = mapped_column(primary_key=True)
    graph_definition_id: Mapped[str] = mapped_column(
        ForeignKey("graph_definition.id", ondelete="CASCADE"),
        nullable=False,
    )
    node_definition_id: Mapped[str] = mapped_column(
        ForeignKey("node_definition.id", ondelete="CASCADE"),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)

    @declared_attr  # type: ignore[arg-type]
    def __mapper_args__(cls) -> dict[str, Any]:
        return {"version_id_col": cls.version}

    graph_definition_model: Mapped[GraphDefinitionModel] = relationship(
        "GraphDefinitionModel",
    )

    node_definition_model: Mapped[NodeDefinitionModel] = relationship(
        "NodeDefinitionModel",
    )
