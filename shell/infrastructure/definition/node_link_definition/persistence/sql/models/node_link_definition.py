from __future__ import annotations

from datetime import datetime  # noqa: TC003 — SQLAlchemy Mapped[datetime] needs runtime type
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from shell.platform.infrastructure.persistence.sql.models.base import Base
from shell.platform.infrastructure.persistence.sql.models.mixins import VersionedMixin

if TYPE_CHECKING:
    from shell.infrastructure.definition.graph_definition.persistence.sql.models.graph_definition import (
        GraphDefinitionModel,
    )
    from shell.infrastructure.definition.node_definition.persistence.sql.models.node_definition import (
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
    def __mapper_args__(cls) -> dict[str, object]:
        return {"version_id_col": cls.version}

    graph_definition_model: Mapped[GraphDefinitionModel] = relationship(
        "GraphDefinitionModel",
    )

    node_definition_model: Mapped[NodeDefinitionModel] = relationship(
        "NodeDefinitionModel",
    )
