from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from shell.infrastructure.platform.persistence.sql.models.base import Base
from shell.infrastructure.platform.persistence.sql.models.mixins import VersionedMixin

if TYPE_CHECKING:
    from shell.infrastructure.definition.persistence.sql.models.graph_definition import (  # noqa: E402 — łamie circular import GraphNodeDefinitionModel ↔ GraphDefinitionModel
        GraphDefinitionModel,  # noqa: TC002 — GraphDefinitionModel używany w Mapped[GraphDefinitionModel] w relacji SQLAlchemy
    )


class GraphNodeDefinitionModel(Base, VersionedMixin):
    __tablename__ = "graph_node_definition"

    id: Mapped[str] = mapped_column(primary_key=True)
    graph_definition_id: Mapped[str] = mapped_column(
        ForeignKey("graph_definition.id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(nullable=False)
    mode: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(nullable=False)
    node_type: Mapped[str] = mapped_column(nullable=False)
    model: Mapped[str | None] = mapped_column(nullable=True)
    command: Mapped[str] = mapped_column(nullable=False)
    timeout: Mapped[int] = mapped_column(nullable=False)
    retries: Mapped[int] = mapped_column(nullable=False)
    log_level: Mapped[str] = mapped_column(nullable=False)
    max_step: Mapped[int | None] = mapped_column(nullable=True)
    no_ask_user: Mapped[bool | None] = mapped_column(nullable=True)
    autopilot: Mapped[bool | None] = mapped_column(nullable=True)
    status_initial: Mapped[str] = mapped_column(nullable=False)
    script: Mapped[str | None] = mapped_column(nullable=True)
    script_type: Mapped[str | None] = mapped_column(nullable=True)

    @declared_attr  # type: ignore[arg-type]  # SQLAlchemy stubs expect Mapped[T], but __mapper_args__ returns dict
    def __mapper_args__(cls) -> dict[str, Any]:
        return {"version_id_col": cls.version}

    graph_definition_model: Mapped[GraphDefinitionModel] = relationship(
        "GraphDefinitionModel",
        back_populates="graph_node_execution_models",
    )
