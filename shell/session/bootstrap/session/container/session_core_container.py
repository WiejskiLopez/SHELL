"""SessionCoreContainer — minimal DI container for the standalone Session BC microservice."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.infrastructure.identity.uuid_id_generator import UuidIdGenerator
from shell.platform.infrastructure.logging.stdlib_logger import StdlibLogger
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.platform.infrastructure.time.system_clock import SystemClock
from shell.session.application.session.session.command_handlers.close_session_handler import (
    CloseSessionHandler,
)
from shell.session.application.session.session.command_handlers.delete_session_handler import (
    DeleteSessionHandler,
)
from shell.session.application.session.session.command_handlers.open_session_handler import (
    OpenSessionHandler,
)
from shell.session.application.session.session.command_handlers.update_session_handler import (
    UpdateSessionHandler,
)
from shell.session.application.session.session.commands.close_session_command import (
    CloseSessionCommand,
)
from shell.session.application.session.session.commands.delete_session_command import (
    DeleteSessionCommand,
)
from shell.session.application.session.session.commands.open_session_command import (
    OpenSessionCommand,
)
from shell.session.application.session.session.commands.update_session_command import (
    UpdateSessionCommand,
)
from shell.session.application.session.session.queries.get_session_history_query import (
    GetSessionHistoryQuery,
)
from shell.session.application.session.session.queries.list_sessions_query import ListSessionsQuery
from shell.session.application.session.session.query_handlers.get_session_history_handler import (
    GetSessionHistoryHandler,
)
from shell.session.application.session.session.query_handlers.list_sessions_handler import (
    ListSessionsHandler,
)
from shell.session.infrastructure.session.session.persistence.sql.services.session_query_service import (
    SessionQueryService,
)
from shell.session.infrastructure.session.session.persistence.sql.unit_of_work import (
    SqlAlchemySessionUnitOfWork,
)


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

    session_query_service = providers.Singleton(
        SessionQueryService,
        session_factory=session_factory,
    )

    open_session_handler_factory = providers.Factory(
        OpenSessionHandler,
        unit_of_work=unit_of_work_factory,
        clock=clock_factory,
        id_generator=id_generator_factory,
    )
    close_session_handler_factory = providers.Factory(
        CloseSessionHandler,
        unit_of_work=unit_of_work_factory,
        clock=clock_factory,
    )
    update_session_handler_factory = providers.Factory(
        UpdateSessionHandler,
        unit_of_work=unit_of_work_factory,
        clock=clock_factory,
    )
    delete_session_handler_factory = providers.Factory(
        DeleteSessionHandler,
        unit_of_work=unit_of_work_factory,
        clock=clock_factory,
    )
    get_session_history_handler_factory = providers.Factory(
        GetSessionHistoryHandler,
        queries=session_query_service,
    )
    list_sessions_handler_factory = providers.Factory(
        ListSessionsHandler,
        queries=session_query_service,
    )


def configure_session_container(container: SessionCoreContainer) -> None:
    """Register Session BC commands and queries on its local buses."""

    command_bus = container.command_bus()
    query_bus = container.query_bus()

    command_bus.register(OpenSessionCommand, container.open_session_handler_factory)
    command_bus.register(CloseSessionCommand, container.close_session_handler_factory)
    command_bus.register(UpdateSessionCommand, container.update_session_handler_factory)
    command_bus.register(DeleteSessionCommand, container.delete_session_handler_factory)

    query_bus.register(GetSessionHistoryQuery, container.get_session_history_handler_factory)
    query_bus.register(ListSessionsQuery, container.list_sessions_handler_factory)
