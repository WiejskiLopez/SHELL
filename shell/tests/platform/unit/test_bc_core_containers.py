from __future__ import annotations

from shell.session_service.application.session.session.commands.close_session_command import (
    CloseSessionCommand,
)
from shell.session_service.application.session.session.commands.delete_session_command import (
    DeleteSessionCommand,
)
from shell.session_service.application.session.session.commands.open_session_command import (
    OpenSessionCommand,
)
from shell.session_service.application.session.session.commands.update_session_command import (
    UpdateSessionCommand,
)
from shell.session_service.application.session.session.queries.get_session_by_id_query import (
    GetSessionByIdQuery,
)
from shell.session_service.application.session.session.queries.get_session_history_query import (
    GetSessionHistoryQuery,
)
from shell.session_service.application.session.session.queries.list_sessions_query import (
    ListSessionsQuery,
)
from shell.session_service.application.session.session.query_handlers.get_session_history_handler import (
    GetSessionHistoryHandler,
)
from shell.session_service.application.session.session_state.queries.get_session_state_by_id_query import (
    GetSessionStateByIdQuery,
)
from shell.session_service.bootstrap.session.container.session_core_container import (
    SessionCoreContainer,
    configure_session_container,
)


def test_session_core_container_registers_only_session_handlers() -> None:
    container = SessionCoreContainer()
    container.config.db_url.from_value("sqlite+aiosqlite:///:memory:")

    configure_session_container(container)

    assert set(container.command_bus()._handler_factories) == {
        OpenSessionCommand,
        CloseSessionCommand,
        UpdateSessionCommand,
        DeleteSessionCommand,
    }
    assert set(container.query_bus()._factories) == {
        GetSessionHistoryQuery,
        GetSessionByIdQuery,
        ListSessionsQuery,
        GetSessionStateByIdQuery,
    }
    assert type(container.get_session_history_handler_factory()) is GetSessionHistoryHandler
