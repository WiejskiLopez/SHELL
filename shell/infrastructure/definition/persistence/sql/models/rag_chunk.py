from __future__ import annotations

from shell.infrastructure.platform.persistence.sql.models.base import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


class RagChunkModel(Base):
    __tablename__ = "rag_chunk"

    id: Mapped[str] = mapped_column(primary_key=True)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("rag_document.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(nullable=False, default=0)
    chunk_text: Mapped[str] = mapped_column(nullable=False)
    embedding: Mapped[bytes] = mapped_column(nullable=False)
    embedding_model: Mapped[str] = mapped_column(nullable=False)

    document: Mapped[RagDocumentModel] = relationship("RagDocumentModel", back_populates="chunks")


from shell.infrastructure.definition.persistence.sql.models.rag_document import (  # noqa: E402 — łamie circular import RagChunkModel ↔ RagDocumentModel
    RagDocumentModel,  # noqa: TC002 — RagDocumentModel używany w Mapped[RagDocumentModel] w relacji SQLAlchemy
)
