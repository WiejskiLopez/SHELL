from __future__ import annotations

from datetime import (
    datetime,  # noqa: TC003 - SQLAlchemy resolves Mapped[...] at class definition
)

from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from shell.definition_service.infrastructure.definition.persistence.sql.models.base import (
    DefinitionSqlAlchemyModelBase,
)
from shell.platform.infrastructure.persistence.sql.models.mixins import VersionedMixin


class GraphDefinitionModel(DefinitionSqlAlchemyModelBase, VersionedMixin):
    __tablename__ = "graph_definition"

    id: Mapped[str] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    @declared_attr  # type: ignore[arg-type]
    def __mapper_args__(cls) -> dict[str, object]:
        return {"version_id_col": cls.version}
