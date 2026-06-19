from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship

from shell.infrastructure.platform.persistence.sql.models.base import Base


class GraphDefinitionModel(Base):
    __tablename__ = "graph_definition"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    purpose: Mapped[str] = mapped_column(nullable=False)

    graph_node_execution_models: Mapped[list[GraphNodeDefinitionModel]] = relationship(
        "GraphNodeDefinitionModel",
        back_populates="graph_definition_model",
        cascade="all, delete-orphan",
        order_by="GraphNodeDefinitionModel.position",
    )

    graph_node_transition_definition_models: Mapped[list[GraphNodeTransitionDefinitionModel]] = relationship(
        "GraphNodeTransitionDefinitionModel",
        back_populates="graph_definition_model",
        cascade="all, delete-orphan",
    )


from shell.infrastructure.definition.persistence.sql.models.graph_node_definition import GraphNodeDefinitionModel
from shell.infrastructure.definition.persistence.sql.models.graph_node_transition_definition import GraphNodeTransitionDefinitionModel
