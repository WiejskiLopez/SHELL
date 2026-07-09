"""MessagingCoreContainer - minimalny kontener DI dla samodzielnego mikroserwisu Messaging BC."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.application.messaging.query_handlers.get_message_by_id_handler import (
    GetMessageByIdHandler,
)
from shell.application.platform.bus.message_bus import MessageBus
from shell.infrastructure.messaging.persistence.sql.services.message_router_query_service import (
    MessageRouterQueryService,
)
from shell.infrastructure.platform.identity.uuid_id_generator import UuidIdGenerator
from shell.infrastructure.platform.logging.stdlib_logger import StdlibLogger
from shell.infrastructure.platform.persistence.sql import build_session_factory
from shell.infrastructure.platform.time.system_clock import SystemClock


class MessagingCoreContainer(containers.DeclarativeContainer):
    """Minimalny kontener dla BC Messaging — używany przy starcie mikroserwisu messaging."""

    config = providers.Configuration()

    # Baza danych
    session_factory = providers.Singleton(build_session_factory, url=config.db_url)

    # Query service
    message_router_query_service = providers.Singleton(
        MessageRouterQueryService, session_factory=session_factory
    )

    # Query handler
    get_message_handler_factory = providers.Factory(
        GetMessageByIdHandler, queries=message_router_query_service
    )

    # Narzędzia wspólne
    clock_factory = providers.Factory(SystemClock)
    id_generator_factory = providers.Factory(UuidIdGenerator)
    stdlib_logger = providers.Singleton(StdlibLogger, name="shell.messaging")

    # Szyny aplikacyjne
    message_bus = providers.Singleton(MessageBus)
