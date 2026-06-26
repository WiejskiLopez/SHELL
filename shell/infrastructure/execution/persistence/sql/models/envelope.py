from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] wymaga datetime w runtime

from shell.infrastructure.platform.persistence.sql.models._compat import JSONB
from shell.infrastructure.platform.persistence.sql.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr
from shell.infrastructure.platform.persistence.sql.models.mixins import VersionedMixin


class EnvelopeModel(Base, VersionedMixin):
    __tablename__ = "envelope"

    id: Mapped[str] = mapped_column(primary_key=True)
    workflow_id: Mapped[str] = mapped_column(nullable=False)
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

    @declared_attr
    def __mapper_args__(cls) -> dict:
        return {"version_id_col": cls.version}

    events: Mapped[list[EnvelopeEventModel]] = relationship(
        "EnvelopeEventModel", back_populates="envelope", cascade="all, delete-orphan"
    )


from shell.infrastructure.execution.persistence.sql.models.envelope_event import (  # noqa: E402 — łamie circular import EnvelopeModel ↔ EnvelopeEventModel
    EnvelopeEventModel,  # noqa: TC002 — EnvelopeEventModel używany w Mapped[list[EnvelopeEventModel]] w relacji SQLAlchemy
)
