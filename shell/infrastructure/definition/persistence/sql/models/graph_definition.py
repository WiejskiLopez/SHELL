from __future__ import annotations

from shell.infrastructure.platform.persistence.sql.models.base import Base
from shell.infrastructure.platform.persistence.sql.models.mixins import VersionedMixin
from sqlalchemy import String
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship


class GraphDefinitionModel(Base, VersionedMixin):
    __tablename__ = "graph_definition"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    purpose: Mapped[str] = mapped_column(nullable=False)
    system_role: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)

    @declared_attr  # type: ignore[arg-type]
    def __mapper_args__(cls) -> dict:
        return {"version_id_col": cls.version}

    graph_node_execution_models: Mapped[list[GraphNodeDefinitionModel]] = relationship(
        "GraphNodeDefinitionModel",
        back_populates="graph_definition_model",
        cascade="all, delete-orphan",
        order_by="GraphNodeDefinitionModel.position",
    )

    graph_node_transition_definition_models: Mapped[list[GraphNodeTransitionDefinitionModel]] = (
        relationship(
            "GraphNodeTransitionDefinitionModel",
            back_populates="graph_definition_model",
            cascade="all, delete-orphan",
        )
    )


from shell.infrastructure.definition.persistence.sql.models.graph_node_definition import (  # noqa: E402 — łamie circular import GraphDefinitionModel ↔ GraphNodeDefinitionModel
    GraphNodeDefinitionModel,  # noqa: TC002 — GraphNodeDefinitionModel używany w Mapped[list[GraphNodeDefinitionModel]] w relacji SQLAlchemy
)
from shell.infrastructure.definition.persistence.sql.models.graph_node_transition_definition import (  # noqa: E402 — łamie circular import GraphDefinitionModel ↔ GraphNodeTransitionDefinitionModel
    GraphNodeTransitionDefinitionModel,  # noqa: TC002 — GraphNodeTransitionDefinitionModel używany w Mapped[list[...]] w relacji SQLAlchemy
)
