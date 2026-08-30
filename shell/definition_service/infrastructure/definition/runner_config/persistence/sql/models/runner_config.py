from __future__ import annotations

from datetime import datetime  # noqa: TC003 - SQLAlchemy resolves Mapped[...] at class definition

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from shell.definition_service.infrastructure.definition.persistence.sql.models.base import (
    DefinitionSqlAlchemyModelBase,
)
from shell.platform.infrastructure.persistence.sql.models.mixins import VersionedMixin


class RunnerConfigModel(DefinitionSqlAlchemyModelBase, VersionedMixin):
    __tablename__ = "runner_config"

    id: Mapped[str] = mapped_column(primary_key=True)
    package_name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    hash: Mapped[str] = mapped_column(String(64), nullable=False)
    body: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    version: Mapped[int] = mapped_column(nullable=False, default=1)

    @declared_attr  # type: ignore[arg-type]
    def __mapper_args__(cls) -> dict[str, object]:
        return {"version_id_col": cls.version}
