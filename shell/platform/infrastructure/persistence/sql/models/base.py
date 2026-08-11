from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class SqlAlchemyModelBase(DeclarativeBase):
    pass


Base = SqlAlchemyModelBase
