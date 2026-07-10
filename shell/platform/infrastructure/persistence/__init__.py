from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # These are only visible to mypy/type checkers — not imported at runtime.
    # Runtime access is handled by __getattr__ below to break the circular import:
    # SqlAlchemyUnitOfWork -> scheduling repos -> models -> platform.persistence (this module)
    from shell.platform.infrastructure.persistence.in_memory_repository import InMemoryRepository
    from shell.platform.infrastructure.persistence.sql_alchemy_uow import SqlAlchemyUnitOfWork
    from shell.platform.infrastructure.persistence.sql_alchemy_uow_base import (
        SqlAlchemyUnitOfWorkBase,
    )

__all__ = ["InMemoryRepository", "SqlAlchemyUnitOfWork", "SqlAlchemyUnitOfWorkBase"]


def __getattr__(name: str) -> object:
    if name == "SqlAlchemyUnitOfWork":
        from shell.platform.infrastructure.persistence.sql_alchemy_uow import (  # noqa: PLC0415 -- deferred to break circular import chain
            SqlAlchemyUnitOfWork,
        )

        return SqlAlchemyUnitOfWork
    if name == "SqlAlchemyUnitOfWorkBase":
        from shell.platform.infrastructure.persistence.sql_alchemy_uow_base import (  # noqa: PLC0415 -- deferred to break circular import chain
            SqlAlchemyUnitOfWorkBase,
        )

        return SqlAlchemyUnitOfWorkBase
    if name == "InMemoryRepository":
        from shell.platform.infrastructure.persistence.in_memory_repository import (  # noqa: PLC0415 -- deferred to break circular import chain
            InMemoryRepository,
        )

        return InMemoryRepository
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
