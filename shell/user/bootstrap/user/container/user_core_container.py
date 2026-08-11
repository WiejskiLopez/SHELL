"""UserCoreContainer — minimal DI container for the standalone User BC microservice."""

from __future__ import annotations

from datetime import timedelta

from dependency_injector import containers, providers

from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.infrastructure.identity.uuid_id_generator import UuidIdGenerator
from shell.platform.infrastructure.logging.stdlib_logger import StdlibLogger
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.platform.infrastructure.time.system_clock import SystemClock
from shell.user.application.user.auth_session.command_handlers.login_auth_session_handler import (
    LoginAuthSessionHandler,
)
from shell.user.application.user.auth_session.command_handlers.logout_auth_session_handler import (
    LogoutAuthSessionHandler,
)
from shell.user.application.user.auth_session.commands.login_auth_session_command import (
    LoginAuthSessionCommand,
)
from shell.user.application.user.auth_session.commands.logout_auth_session_command import (
    LogoutAuthSessionCommand,
)
from shell.user.application.user.auth_session.queries.get_current_auth_session_query import (
    GetCurrentAuthSessionQuery,
)
from shell.user.application.user.auth_session.query_handlers.get_current_auth_session_handler import (
    GetCurrentAuthSessionHandler,
)
from shell.user.application.user.user.command_handlers.create_user_handler import CreateUserHandler
from shell.user.application.user.user.command_handlers.delete_user_handler import DeleteUserHandler
from shell.user.application.user.user.command_handlers.update_user_handler import UpdateUserHandler
from shell.user.application.user.user.commands.create_user_command import CreateUserCommand
from shell.user.application.user.user.commands.delete_user_command import DeleteUserCommand
from shell.user.application.user.user.commands.update_user_command import UpdateUserCommand
from shell.user.application.user.user.queries.get_user_by_email_query import GetUserByEmailQuery
from shell.user.application.user.user.queries.get_user_by_id_query import GetUserByIdQuery
from shell.user.application.user.user.queries.list_users_query import ListUsersQuery
from shell.user.application.user.user.query_handlers.get_user_by_email_handler import (
    GetUserByEmailHandler,
)
from shell.user.application.user.user.query_handlers.get_user_by_id_handler import (
    GetUserByIdHandler,
)
from shell.user.application.user.user.query_handlers.list_users_handler import ListUsersHandler
from shell.user.infrastructure.user.auth_session.persistence.sql.services.auth_session_query_service import (
    AuthSessionQueryService,
)
from shell.user.infrastructure.user.auth_session.services.secure_token_generator import (
    SecureTokenGenerator,
)
from shell.user.infrastructure.user.auth_session.services.user_query_provider import (
    SqlUserQueryProvider,
)
from shell.user.infrastructure.user.user.persistence.sql.services.user_query_service import (
    UserQueryService,
)
from shell.user.infrastructure.user.user.persistence.sql.unit_of_work import (
    SqlAlchemyUserUnitOfWork,
)


class UserCoreContainer(containers.DeclarativeContainer):
    """Minimal container for BC User — used when starting the user microservice."""

    config = providers.Configuration()

    # Infrastruktura bazodanowa
    session_factory = providers.Singleton(build_session_factory, url=config.db_url)

    # Per-BC Unit of Work — zna TYLKO repozytoria BC User
    unit_of_work_factory = providers.Factory(
        SqlAlchemyUserUnitOfWork,
        session_factory=session_factory,
    )

    # Shared tools
    clock_factory = providers.Factory(SystemClock)
    id_generator_factory = providers.Factory(UuidIdGenerator)
    stdlib_logger = providers.Singleton(StdlibLogger, name="shell.user")

    # Application buses
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

    user_query_service = providers.Singleton(
        UserQueryService,
        session_factory=session_factory,
    )
    get_user_by_id_handler_factory = providers.Factory(
        GetUserByIdHandler,
        queries=user_query_service,
    )
    get_user_by_email_handler_factory = providers.Factory(
        GetUserByEmailHandler,
        queries=user_query_service,
    )
    list_users_handler_factory = providers.Factory(
        ListUsersHandler,
        queries=user_query_service,
    )

    auth_session_query_service = providers.Singleton(
        AuthSessionQueryService,
        session_factory=session_factory,
    )
    user_query_provider = providers.Singleton(
        SqlUserQueryProvider,
        queries=user_query_service,
    )
    token_generator_factory = providers.Factory(SecureTokenGenerator)
    login_auth_session_handler_factory = providers.Factory(
        LoginAuthSessionHandler,
        unit_of_work=unit_of_work_factory,
        user_query_provider=user_query_provider,
        clock=clock_factory,
        token_generator=token_generator_factory,
        id_generator=id_generator_factory,
        session_ttl=timedelta(hours=24),
    )
    logout_auth_session_handler_factory = providers.Factory(
        LogoutAuthSessionHandler,
        unit_of_work=unit_of_work_factory,
        clock=clock_factory,
    )
    get_current_auth_session_handler_factory = providers.Factory(
        GetCurrentAuthSessionHandler,
        queries=auth_session_query_service,
        clock=clock_factory,
    )


def configure_user_container(container: UserCoreContainer) -> None:
    """Register User BC commands and queries on its local buses."""

    command_bus = container.command_bus()
    query_bus = container.query_bus()

    command_bus.register(CreateUserCommand, container.create_user_handler_factory)
    command_bus.register(UpdateUserCommand, container.update_user_handler_factory)
    command_bus.register(DeleteUserCommand, container.delete_user_handler_factory)
    command_bus.register(
        LoginAuthSessionCommand,
        container.login_auth_session_handler_factory,
    )
    command_bus.register(
        LogoutAuthSessionCommand,
        container.logout_auth_session_handler_factory,
    )

    query_bus.register(GetUserByIdQuery, container.get_user_by_id_handler_factory)
    query_bus.register(GetUserByEmailQuery, container.get_user_by_email_handler_factory)
    query_bus.register(ListUsersQuery, container.list_users_handler_factory)
    query_bus.register(
        GetCurrentAuthSessionQuery,
        container.get_current_auth_session_handler_factory,
    )
