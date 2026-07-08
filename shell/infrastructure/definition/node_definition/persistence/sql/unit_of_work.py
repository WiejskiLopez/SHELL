from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.repositories.graph_definition_repository.node_definition_repository import (
    NodeDefinitionRepository,
)
from shell.infrastructure.definition.node_definition.persistence.sql.repositories.sql_node_definition_repository import (
    SqlNodeDefinitionRepository,
)
from shell.infrastructure.platform.persistence.sql_alchemy_uow_base import (
    SqlAlchemyUnitOfWorkBase,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

_REPO_MAP: dict[type, type] = {
    NodeDefinitionRepository: SqlNodeDefinitionRepository,
}


class SqlAlchemyNodeDefinitionUnitOfWork(SqlAlchemyUnitOfWorkBase):
    def __init__(self, session_factory: async_sessionmaker) -> None:
        super().__init__(session_factory)

    def _build_repo_map(self) -> dict[type, type]:
        return _REPO_MAP
