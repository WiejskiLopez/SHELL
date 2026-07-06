"""SqlAlchemyDefinitionUnitOfWork — UoW dedykowany dla BC Definition."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from shell.domain.definition.aggregates.graph_definition_embedding.repositories.graph_definition_embedding_repository import (
    GraphDefinitionEmbeddingRepository,
)
from shell.domain.definition.repositories.graph_definition_repository.graph_definition_repository import (
    GraphDefinitionRepository,
)
from shell.domain.definition.repositories.graph_definition_repository.node_definition_repository import (
    NodeDefinitionRepository,
)
from shell.domain.definition.repositories.rag_repository import RagDocumentRepository
from shell.domain.definition.repositories.runner_config_repository import RunnerConfigRepository
from shell.infrastructure.definition.persistence.sql.repositories import (
    SqlGraphDefinitionEmbeddingRepository,
    SqlGraphDefinitionRepository,
    SqlNodeDefinitionRepository,
    SqlRagDocumentRepository,
    SqlRunnerConfigRepository,
)
from shell.infrastructure.platform.persistence.sql.rag_search import create_rag_search_strategy
from shell.infrastructure.platform.persistence.sql_alchemy_uow_base import (
    SqlAlchemyUnitOfWorkBase,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

TRepository = TypeVar("TRepository")

_REPO_MAP: dict[type, type] = {
    GraphDefinitionRepository: SqlGraphDefinitionRepository,
    NodeDefinitionRepository: SqlNodeDefinitionRepository,
    GraphDefinitionEmbeddingRepository: SqlGraphDefinitionEmbeddingRepository,
    RunnerConfigRepository: SqlRunnerConfigRepository,
    RagDocumentRepository: SqlRagDocumentRepository,
}


class SqlAlchemyDefinitionUnitOfWork(SqlAlchemyUnitOfWorkBase):
    """UoW dla BC Definition — zna wyłącznie repozytoria warstwy Definition."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        super().__init__(session_factory)
        self._rag_search_strategy = create_rag_search_strategy(session_factory)

    def _build_repo_map(self) -> dict[type, type]:
        return _REPO_MAP

    def repository(self, repo_type: type[TRepository]) -> TRepository:
        """Nadpisuje bazową metodę aby obsłużyć specjalny konstruktor RagDocumentRepository."""
        if repo_type is RagDocumentRepository:
            return SqlRagDocumentRepository(  # type: ignore[return-value]
                self._active_session,
                search_strategy=self._rag_search_strategy,
            )
        return super().repository(repo_type)
