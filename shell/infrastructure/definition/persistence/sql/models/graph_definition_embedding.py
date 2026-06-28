from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from shell.infrastructure.platform.persistence.sql.models.base import Base
from shell.infrastructure.platform.persistence.sql.models.mixins import VersionedMixin


class GraphDefinitionEmbeddingModel(Base, VersionedMixin):
    __tablename__ = "graph_definition_embedding"

    id: Mapped[str] = mapped_column(primary_key=True)
    graph_definition_id: Mapped[str] = mapped_column(
        ForeignKey("graph_definition.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    text: Mapped[str] = mapped_column(nullable=False)
    embedding: Mapped[bytes] = mapped_column(nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(255), nullable=False)
