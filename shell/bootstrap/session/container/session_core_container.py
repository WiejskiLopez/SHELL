"""SessionCoreContainer — minimal DI container for the standalone Session BC microservice."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.infrastructure.session.session.persistence.sql.unit_of_work import (
    SqlAlchemySessionUnitOfWork,
)
from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.infrastructure.identity.uuid_id_generator import UuidIdGenerator
from shell.platform.infrastructure.logging.stdlib_logger import StdlibLogger
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.platform.infrastructure.time.system_clock import SystemClock


class SessionCoreContainer(containers.DeclarativeContainer):
    """Minimal container for BC Session — used when starting the session microservice."""

    config = providers.Configuration()

    # Infrastruktura bazodanowa
    session_factory = providers.Singleton(build_session_factory, url=config.db_url)

    # Per-BC Unit of Work — zna TYLKO repozytoria BC Session
    unit_of_work_factory = providers.Factory(
        SqlAlchemySessionUnitOfWork,
        session_factory=session_factory,
    )

    # Shared tools
    clock_factory = providers.Factory(SystemClock)
    id_generator_factory = providers.Factory(UuidIdGenerator)
    stdlib_logger = providers.Singleton(StdlibLogger, name="shell.session")

    # Application buses
    command_bus = providers.Singleton(CommandBus)
    query_bus = providers.Singleton(QueryBus)

    # Command/Query Handlers dla Session BC można dołączyć tutaj po implementacji.
