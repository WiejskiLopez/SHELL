"""DefinitionCoreContainer — minimal DI container for the Definition BC microservice."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.infrastructure.definition.graph_definition.persistence.sql.services.graph_definition_query_service import (
    SqlGraphDefinitionQueryService,
)
from shell.infrastructure.definition.runner_config.persistence.sql.services.runner_config_query_service import (
    RunnerConfigQueryService,
)
from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.infrastructure.identity.uuid_id_generator import UuidIdGenerator
from shell.platform.infrastructure.logging.stdlib_logger import StdlibLogger
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.platform.infrastructure.time.system_clock import SystemClock


class DefinitionCoreContainer(containers.DeclarativeContainer):
    """Minimal container for BC Definition — used when starting the definition microservice."""

    config = providers.Configuration()

    # Infrastruktura bazodanowa
    session_factory = providers.Singleton(build_session_factory, url=config.db_url)

    # Shared tools
    clock_factory = providers.Factory(SystemClock)
    id_generator_factory = providers.Factory(UuidIdGenerator)
    stdlib_logger = providers.Singleton(StdlibLogger, name="shell.definition")

    # Query services (read-only, bez UoW)
    graph_definition_query_service = providers.Singleton(
        SqlGraphDefinitionQueryService,
        session_factory=session_factory,
    )
    runner_config_query_service = providers.Singleton(
        RunnerConfigQueryService, session_factory=session_factory
    )

    # Application buses
    command_bus = providers.Singleton(CommandBus)
    query_bus = providers.Singleton(QueryBus)
