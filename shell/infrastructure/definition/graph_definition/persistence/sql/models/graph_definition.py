from __future__ import annotations

from datetime import (
    datetime,  # noqa: TC003 — needed by SQLAlchemy ORM at runtime for Mapped[datetime]
)

from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from shell.platform.infrastructure.persistence.sql.models.base import Base
from shell.platform.infrastructure.persistence.sql.models.mixins import VersionedMixin


class GraphDefinitionModel(Base, VersionedMixin):
    __tablename__ = "graph_definition"

    id: Mapped[str] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    @declared_attr  # type: ignore[arg-type]
    def __mapper_args__(cls) -> dict[str, object]:
        return {"version_id_col": cls.version}
