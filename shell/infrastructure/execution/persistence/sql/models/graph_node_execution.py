from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from shell.infrastructure.platform.persistence.sql.models.base import Base
from shell.infrastructure.platform.persistence.sql.models.mixins import VersionedMixin

if TYPE_CHECKING:
    from shell.infrastructure.execution.persistence.sql.models.graph_execution import (  # noqa: E402 — łamie circular import GraphNodeExecutionModel ↔ GraphExecutionModel
        GraphExecutionModel,  # noqa: TC002 — GraphExecutionModel używany w Mapped[GraphExecutionModel] w relacji SQLAlchemy
    )


class GraphNodeExecutionModel(Base, VersionedMixin):
    __tablename__ = "graph_node_execution"

    id: Mapped[str] = mapped_column(primary_key=True)
    graph_execution_id: Mapped[str] = mapped_column(
        ForeignKey("graph_execution.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(nullable=False, default=0)
    mode: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(nullable=False, default="")
    node_type: Mapped[str] = mapped_column(nullable=False, default="")
    model: Mapped[str] = mapped_column(nullable=False, default="")
    command: Mapped[str] = mapped_column(nullable=False, default="")
    retries: Mapped[int] = mapped_column(nullable=False, default=0)
    log_level: Mapped[str] = mapped_column(nullable=False, default="INFO")
    max_step: Mapped[int] = mapped_column(nullable=False, default=0)
    no_ask_user: Mapped[bool] = mapped_column(nullable=False, default=False)
    autopilot: Mapped[bool] = mapped_column(nullable=False, default=False)
    task_execution_id: Mapped[str] = mapped_column(nullable=False, default="")
    source_dir: Mapped[str] = mapped_column(nullable=False, default="")
    status: Mapped[str] = mapped_column(nullable=False, default="pending")
    status_initial: Mapped[str] = mapped_column(nullable=False, default="")
    timeout_seconds: Mapped[int] = mapped_column(nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(nullable=False, default=0)
    retry_delay_seconds: Mapped[int] = mapped_column(nullable=False, default=0)

    @declared_attr  # type: ignore[arg-type]  # SQLAlchemy stubs expect Mapped[T], but __mapper_args__ returns dict
    def __mapper_args__(cls) -> dict[str, Any]:
        return {"version_id_col": cls.version}

    graph_execution_model: Mapped[GraphExecutionModel] = relationship(
        "GraphExecutionModel", back_populates="graph_node_execution_models"
    )
