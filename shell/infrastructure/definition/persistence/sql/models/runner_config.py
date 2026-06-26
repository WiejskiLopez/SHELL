from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Mapped[datetime] wymaga datetime w runtime

from shell.infrastructure.platform.persistence.sql.models._compat import JSONB
from shell.infrastructure.platform.persistence.sql.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column, declared_attr
from shell.infrastructure.platform.persistence.sql.models.mixins import VersionedMixin


class RunnerConfigModel(Base, VersionedMixin):
    __tablename__ = "runner_config"

    id: Mapped[str] = mapped_column(primary_key=True)
    package_name: Mapped[str] = mapped_column(nullable=False)
    kind: Mapped[str] = mapped_column(nullable=False)
    hash: Mapped[str] = mapped_column(nullable=False)
    body: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    @declared_attr
    def __mapper_args__(cls) -> dict:
        return {"version_id_col": cls.version}
