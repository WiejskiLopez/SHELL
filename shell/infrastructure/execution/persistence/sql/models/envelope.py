from __future__ import annotations

from datetime import datetime

from shell.infrastructure.platform.persistence.sql.models._compat import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shell.infrastructure.platform.persistence.sql.models.base import Base


class EnvelopeModel(Base):
    __tablename__ = "envelope"

    id: Mapped[str] = mapped_column(primary_key=True)
    workflow_id: Mapped[str] = mapped_column(nullable=False, index=True)
    parent_id: Mapped[str | None] = mapped_column(nullable=True)
    correlation_id: Mapped[str] = mapped_column(nullable=False, default="")
    sender_graph_node_execution_id: Mapped[str] = mapped_column(nullable=False)
    receiver_graph_node_execution_id: Mapped[str] = mapped_column(nullable=False)
    source_role: Mapped[str] = mapped_column(nullable=False, default="")
    target_role: Mapped[str] = mapped_column(nullable=False, default="")
    sequence_id: Mapped[int] = mapped_column(nullable=False, default=0)
    step: Mapped[int] = mapped_column(nullable=False, default=0)
    status: Mapped[str] = mapped_column(nullable=False, default="pending")
    stage: Mapped[str] = mapped_column(nullable=False, default="draft")
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    artifact_uri: Mapped[str] = mapped_column(nullable=False, default="")
    archive_uri: Mapped[str] = mapped_column(nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)

    events: Mapped[list[EnvelopeEventModel]] = relationship(
        "EnvelopeEventModel", back_populates="envelope", cascade="all, delete-orphan"
    )


from shell.infrastructure.execution.persistence.sql.models.envelope_event import EnvelopeEventModel
