from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import String
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from shell.infrastructure.platform.persistence.sql.models.base import Base
from shell.infrastructure.platform.persistence.sql.models.mixins import VersionedMixin

if TYPE_CHECKING:
    from shell.infrastructure.definition.persistence.sql.models.graph_node_transition_definition import (
        GraphNodeTransitionDefinitionModel,
    )


class GraphDefinitionModel(Base, VersionedMixin):
    __tablename__ = "graph_definition"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    purpose: Mapped[str] = mapped_column(nullable=False)
    system_role: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)

    @declared_attr
    def __mapper_args__(cls) -> dict[str, Any]:
        return {"version_id_col": cls.version}

    graph_node_transition_definition_models: Mapped[list[GraphNodeTransitionDefinitionModel]] = (
        relationship(
            "GraphNodeTransitionDefinitionModel",
            back_populates="graph_definition_model",
            cascade="all, delete-orphan",
        )
    )
