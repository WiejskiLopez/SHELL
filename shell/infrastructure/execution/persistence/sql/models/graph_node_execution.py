from __future__ import annotations

from shell.infrastructure.platform.persistence.sql.models.base import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


class GraphNodeExecutionModel(Base):
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
    timeout: Mapped[int] = mapped_column(nullable=False, default=0)
    retries: Mapped[int] = mapped_column(nullable=False, default=0)
    log_level: Mapped[str] = mapped_column(nullable=False, default="INFO")
    max_step: Mapped[int] = mapped_column(nullable=False, default=0)
    no_ask_user: Mapped[bool] = mapped_column(nullable=False, default=False)
    autopilot: Mapped[bool] = mapped_column(nullable=False, default=False)
    task_execution_id: Mapped[str] = mapped_column(nullable=False, default="")
    source_dir: Mapped[str] = mapped_column(nullable=False, default="")
    status_initial: Mapped[str] = mapped_column(nullable=False, default="")
    timeout_seconds: Mapped[int] = mapped_column(nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(nullable=False, default=0)
    retry_delay_seconds: Mapped[int] = mapped_column(nullable=False, default=0)

    graph_execution_model: Mapped[GraphExecutionModel] = relationship(
        "GraphExecutionModel", back_populates="graph_node_execution_models"
    )

    input_state_models: Mapped[list[GraphNodeExecutionStateInputModel]] = relationship(
        "GraphNodeExecutionStateInputModel",
        back_populates="graph_node_execution_model",
        cascade="all, delete-orphan",
    )

    output_state_models: Mapped[list[GraphNodeExecutionStateOutputModel]] = relationship(
        "GraphNodeExecutionStateOutputModel",
        back_populates="graph_node_execution_model",
        cascade="all, delete-orphan",
    )


from shell.infrastructure.execution.persistence.sql.models.graph_execution import (  # noqa: E402 — łamie circular import GraphNodeExecutionModel ↔ GraphExecutionModel
    GraphExecutionModel,  # noqa: TC002 — GraphExecutionModel używany w Mapped[GraphExecutionModel] w relacji SQLAlchemy
)
from shell.infrastructure.execution.persistence.sql.models.graph_node_execution_state_input import (  # noqa: E402 — łamie circular import GraphNodeExecutionModel ↔ GraphNodeExecutionStateInputModel
    GraphNodeExecutionStateInputModel,  # noqa: TC002 — GraphNodeExecutionStateInputModel używany w Mapped[list[...]] w relacji SQLAlchemy
)
from shell.infrastructure.execution.persistence.sql.models.graph_node_execution_state_output import (  # noqa: E402 — łamie circular import GraphNodeExecutionModel ↔ GraphNodeExecutionStateOutputModel
    GraphNodeExecutionStateOutputModel,  # noqa: TC002 — GraphNodeExecutionStateOutputModel używany w Mapped[list[...]] w relacji SQLAlchemy
)
