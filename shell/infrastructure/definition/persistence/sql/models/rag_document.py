from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] wymaga datetime w runtime

from shell.infrastructure.platform.persistence.sql.models.base import Base
from shell.infrastructure.platform.persistence.sql.models.mixins import VersionedMixin
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship


class RagDocumentModel(Base, VersionedMixin):
    __tablename__ = "rag_document"

    id: Mapped[str] = mapped_column(primary_key=True)
    source_uri: Mapped[str] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    domain: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    @declared_attr
    def __mapper_args__(cls) -> dict:
        return {"version_id_col": cls.version}

    chunks: Mapped[list[RagChunkModel]] = relationship(
        "RagChunkModel", back_populates="document", cascade="all, delete-orphan"
    )


from shell.infrastructure.definition.persistence.sql.models.rag_chunk import (  # noqa: E402 — łamie circular import RagDocumentModel ↔ RagChunkModel
    RagChunkModel,  # noqa: TC002 — RagChunkModel używany w Mapped[list[RagChunkModel]] w relacji SQLAlchemy
)
