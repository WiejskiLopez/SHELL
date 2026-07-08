"""SessionCoreContainer — minimalny kontener DI dla samodzielnego mikroserwisu Session BC."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.application.platform.bus.command_bus import CommandBus
from shell.application.platform.bus.query_bus import QueryBus
from shell.infrastructure.platform.identity.uuid_id_generator import UuidIdGenerator
from shell.infrastructure.platform.logging.stdlib_logger import StdlibLogger
from shell.infrastructure.platform.persistence.sql import build_session_factory
from shell.infrastructure.platform.time.system_clock import SystemClock
from shell.infrastructure.session.session.persistence.sql.unit_of_work import (
    SqlAlchemySessionUnitOfWork,
)


class SessionCoreContainer(containers.DeclarativeContainer):
    """Minimalny kontener dla BC Session — używany przy starcie mikroserwisu session."""

    config = providers.Configuration()

    # Infrastruktura bazodanowa
    session_factory = providers.Singleton(build_session_factory, url=config.db_url)

    # Per-BC Unit of Work — zna TYLKO repozytoria BC Session
    unit_of_work_factory = providers.Factory(
        SqlAlchemySessionUnitOfWork,
        session_factory=session_factory,
    )

    # Narzędzia wspólne
    clock_factory = providers.Factory(SystemClock)
    id_generator_factory = providers.Factory(UuidIdGenerator)
    stdlib_logger = providers.Singleton(StdlibLogger, name="shell.session")

    # Szyny aplikacyjne
    command_bus = providers.Singleton(CommandBus)
    query_bus = providers.Singleton(QueryBus)

    # Command/Query Handlers dla Session BC można dołączyć tutaj po implementacji.
