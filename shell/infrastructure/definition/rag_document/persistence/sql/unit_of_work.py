from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from shell.domain.definition.repositories.rag_repository import RagDocumentRepository
from shell.infrastructure.definition.rag_document.persistence.sql.repositories.sql_rag_document_repository import (
    SqlRagDocumentRepository,
)
from shell.infrastructure.definition.rag_document.persistence.sql.search import (
    create_rag_search_strategy,
)
from shell.infrastructure.platform.persistence.sql_alchemy_uow_base import (
    SqlAlchemyUnitOfWorkBase,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

TRepository = TypeVar("TRepository")


class SqlAlchemyRagDocumentUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        super().__init__(session_factory)
        self._rag_search_strategy = create_rag_search_strategy(session_factory)

    def _build_repo_map(self) -> dict[type, type]:
        return {}

    def repository(self, repo_type: type[TRepository]) -> TRepository:
        if repo_type is RagDocumentRepository:
            return SqlRagDocumentRepository(  # type: ignore[return-value]
                self._active_session,
                search_strategy=self._rag_search_strategy,
            )
        msg = f"Unknown repository type for RagDocument UoW: {repo_type.__name__}"
        raise ValueError(msg)
