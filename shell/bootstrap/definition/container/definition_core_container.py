"""DefinitionCoreContainer — minimalny kontener DI dla mikroserwisu Definition BC."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.application.platform.bus.command_bus import CommandBus
from shell.application.platform.bus.query_bus import QueryBus
from shell.infrastructure.definition.graph_definition.persistence.sql.services.graph_definition_query_service import (
    SqlGraphDefinitionQueryService,
)
from shell.infrastructure.definition.persistence.sql.services import (
    RagQueryService,
    RunnerConfigQueryService,
)
from shell.infrastructure.definition.persistence.sql_alchemy_definition_uow import (
    SqlAlchemyDefinitionUnitOfWork,
)
from shell.infrastructure.platform.external.hash_embedder import HashEmbedder
from shell.infrastructure.platform.identity.uuid_id_generator import UuidIdGenerator
from shell.infrastructure.platform.logging.stdlib_logger import StdlibLogger
from shell.infrastructure.platform.persistence.sql import build_session_factory
from shell.infrastructure.platform.time.system_clock import SystemClock


class DefinitionCoreContainer(containers.DeclarativeContainer):
    """Minimalny kontener dla BC Definition — używany przy starcie mikroserwisu definition."""

    config = providers.Configuration()

    # Infrastruktura bazodanowa
    session_factory = providers.Singleton(build_session_factory, url=config.db_url)

    # Per-BC Unit of Work — zna TYLKO repozytoria BC Definition
    unit_of_work_factory = providers.Factory(
        SqlAlchemyDefinitionUnitOfWork,
        session_factory=session_factory,
    )

    # Narzędzia wspólne
    clock_factory = providers.Factory(SystemClock)
    id_generator_factory = providers.Factory(UuidIdGenerator)
    stdlib_logger = providers.Singleton(StdlibLogger, name="shell.definition")
    embedder = providers.Singleton(HashEmbedder)

    # Query services (read-only, bez UoW)
    graph_definition_query_service = providers.Singleton(
        SqlGraphDefinitionQueryService,
        session_factory=session_factory,
        embedder=embedder,
    )
    rag_query_service = providers.Singleton(RagQueryService, session_factory=session_factory)
    runner_config_query_service = providers.Singleton(
        RunnerConfigQueryService, session_factory=session_factory
    )

    # Szyny aplikacyjne
    command_bus = providers.Singleton(CommandBus)
    query_bus = providers.Singleton(QueryBus)
