from __future__ import annotations

from datetime import datetime  # noqa: TC003 — SQLAlchemy Mapped[datetime] needs runtime type

from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from shell.definition.infrastructure.definition.persistence.sql.models.base import (
    DefinitionSqlAlchemyModelBase,
)
from shell.platform.infrastructure.persistence.sql.models.mixins import VersionedMixin


class NodeDefinitionModel(DefinitionSqlAlchemyModelBase, VersionedMixin):
    __tablename__ = "node_definition"

    id: Mapped[str] = mapped_column(primary_key=True)
    node_type: Mapped[str] = mapped_column(nullable=False)
    max_step: Mapped[int | None] = mapped_column(nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)

    @declared_attr  # type: ignore[arg-type]
    def __mapper_args__(cls) -> dict[str, object]:
        return {"version_id_col": cls.version}
