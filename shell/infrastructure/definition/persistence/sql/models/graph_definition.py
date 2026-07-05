from __future__ import annotations

from typing import Any

from sqlalchemy import String
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from shell.infrastructure.platform.persistence.sql.models.base import Base
from shell.infrastructure.platform.persistence.sql.models.mixins import VersionedMixin


class GraphDefinitionModel(Base, VersionedMixin):
    __tablename__ = "graph_definition"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    purpose: Mapped[str] = mapped_column(nullable=False)
    system_role: Mapped[str | None] = mapped_column(String(50), nullable=True, unique=True)

    @declared_attr  # type: ignore[arg-type]
    def __mapper_args__(cls) -> dict[str, Any]:
        return {"version_id_col": cls.version}

    