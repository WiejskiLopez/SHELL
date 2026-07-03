from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from shell.infrastructure.platform.persistence.sql.models.base import Base
from shell.infrastructure.platform.persistence.sql.models.mixins import VersionedMixin

if TYPE_CHECKING:
    from shell.infrastructure.definition.persistence.sql.models.graph_definition import (
        GraphDefinitionModel,
    )
    from shell.infrastructure.definition.persistence.sql.models.graph_node_definition import (
        GraphNodeDefinitionModel,
    )


class GraphNodeLinkDefinitionModel(Base, VersionedMixin):
    __tablename__ = "graph_node_link_definition"

    id: Mapped[str] = mapped_column(primary_key=True)
    graph_definition_id: Mapped[str] = mapped_column(
        ForeignKey("graph_definition.id", ondelete="CASCADE"),
        nullable=False,
    )
    graph_node_definition_id: Mapped[str] = mapped_column(
        ForeignKey("graph_node_definition.id", ondelete="CASCADE"),
        nullable=False,
    )

    @declared_attr
    def __mapper_args__(cls) -> dict[str, Any]:
        return {"version_id_col": cls.version}

    graph_definition_model: Mapped[GraphDefinitionModel] = relationship(
        "GraphDefinitionModel",
    )

    graph_node_definition_model: Mapped[GraphNodeDefinitionModel] = relationship(
        "GraphNodeDefinitionModel",
    )
