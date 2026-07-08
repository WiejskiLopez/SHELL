"""MessagingCoreContainer - minimalny kontener DI dla samodzielnego mikroserwisu Messaging BC."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.application.messaging.bus.message_bus import MessageBus
from shell.application.messaging.query_handlers.message_get_by_id_handler import (
    MessageGetByIdHandler,
)
from shell.infrastructure.messaging.persistence.sql.services.message_query_service import (
    MessageQueryService,
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
    message_query_service = providers.Singleton(
        MessageQueryService, session_factory=session_factory
    )

    # Query handler
    get_message_handler_factory = providers.Factory(
        MessageGetByIdHandler, queries=message_query_service
    )

    # Narzędzia wspólne
    clock_factory = providers.Factory(SystemClock)
    id_generator_factory = providers.Factory(UuidIdGenerator)
    stdlib_logger = providers.Singleton(StdlibLogger, name="shell.messaging")

    # Szyny aplikacyjne
    message_bus = providers.Singleton(MessageBus)
