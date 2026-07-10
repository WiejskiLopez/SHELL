"""UserCoreContainer — minimalny kontener DI dla samodzielnego mikroserwisu User BC."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.application.user.user.command_handlers.create_user_handler import CreateUserHandler
from shell.application.user.user.command_handlers.delete_user_handler import DeleteUserHandler
from shell.application.user.user.command_handlers.update_user_handler import UpdateUserHandler
from shell.infrastructure.user.user.persistence.sql.unit_of_work import SqlAlchemyUserUnitOfWork
from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.infrastructure.identity.uuid_id_generator import UuidIdGenerator
from shell.platform.infrastructure.logging.stdlib_logger import StdlibLogger
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.platform.infrastructure.time.system_clock import SystemClock


class UserCoreContainer(containers.DeclarativeContainer):
    """Minimalny kontener dla BC User — używany przy starcie mikroserwisu user."""

    config = providers.Configuration()

    # Infrastruktura bazodanowa
    session_factory = providers.Singleton(build_session_factory, url=config.db_url)

    # Per-BC Unit of Work — zna TYLKO repozytoria BC User
    unit_of_work_factory = providers.Factory(
        SqlAlchemyUserUnitOfWork,
        session_factory=session_factory,
    )

    # Narzędzia wspólne
    clock_factory = providers.Factory(SystemClock)
    id_generator_factory = providers.Factory(UuidIdGenerator)
    stdlib_logger = providers.Singleton(StdlibLogger, name="shell.user")

    # Szyny aplikacyjne
    command_bus = providers.Singleton(CommandBus)
    query_bus = providers.Singleton(QueryBus)

    # Command Handlers — tylko User BC
    create_user_handler_factory = providers.Factory(
        CreateUserHandler,
        unit_of_work=unit_of_work_factory,
        clock=clock_factory,
        id_generator=id_generator_factory,
    )
    update_user_handler_factory = providers.Factory(
        UpdateUserHandler,
        unit_of_work=unit_of_work_factory,
        clock=clock_factory,
    )
    delete_user_handler_factory = providers.Factory(
        DeleteUserHandler,
        unit_of_work=unit_of_work_factory,
        clock=clock_factory,
    )
