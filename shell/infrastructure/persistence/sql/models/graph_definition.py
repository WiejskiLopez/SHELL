from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


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


from .graph_node_definition import GraphNodeDefinitionModel
