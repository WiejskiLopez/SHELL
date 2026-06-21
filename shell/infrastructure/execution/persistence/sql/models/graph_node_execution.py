from __future__ import annotations

from shell.infrastructure.platform.persistence.sql.models._compat import JSONB
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
    sub_graph_definition_id: Mapped[str | None] = mapped_column(nullable=True)
    sub_graph_definition_version: Mapped[int | None] = mapped_column(nullable=True)
    timeout_seconds: Mapped[int] = mapped_column(nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(nullable=False, default=0)
    retry_delay_seconds: Mapped[int] = mapped_column(nullable=False, default=0)
    extra: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    graph_execution_model: Mapped[GraphExecutionModel] = relationship(
        "GraphExecutionModel", back_populates="graph_node_execution_models"
    )

    input_payload_models: Mapped[list[GraphNodeExecutionInputPayloadModel]] = relationship(
        "GraphNodeExecutionInputPayloadModel",
        back_populates="graph_node_execution_model",
        cascade="all, delete-orphan",
    )

    output_payload_models: Mapped[list[GraphNodeExecutionOutputPayloadModel]] = relationship(
        "GraphNodeExecutionOutputPayloadModel",
        back_populates="graph_node_execution_model",
        cascade="all, delete-orphan",
    )


from shell.infrastructure.execution.persistence.sql.models.graph_execution import (  # noqa: E402 — łamie circular import GraphNodeExecutionModel ↔ GraphExecutionModel
    GraphExecutionModel,  # noqa: TC002 — GraphExecutionModel używany w Mapped[GraphExecutionModel] w relacji SQLAlchemy
)
from shell.infrastructure.execution.persistence.sql.models.graph_node_execution_input_payload import (  # noqa: E402 — łamie circular import GraphNodeExecutionModel ↔ GraphNodeExecutionInputPayloadModel
    GraphNodeExecutionInputPayloadModel,  # noqa: TC002 — GraphNodeExecutionInputPayloadModel używany w Mapped[list[...]] w relacji SQLAlchemy
)
from shell.infrastructure.execution.persistence.sql.models.graph_node_execution_output_payload import (  # noqa: E402 — łamie circular import GraphNodeExecutionModel ↔ GraphNodeExecutionOutputPayloadModel
    GraphNodeExecutionOutputPayloadModel,  # noqa: TC002 — GraphNodeExecutionOutputPayloadModel używany w Mapped[list[...]] w relacji SQLAlchemy
)
