from __future__ import annotations

from sqlalchemy import MetaData

from shell.platform.infrastructure.persistence.sql.models.base import SqlAlchemyModelBase


class ProjectSqlAlchemyModelBase(SqlAlchemyModelBase):
    __abstract__ = True
    metadata = MetaData()
