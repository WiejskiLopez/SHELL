from __future__ import annotations

from shell.platform.framework.api.principal import (
    Principal,
    PrincipalKind,
    get_principal,
    require_user_principal,
)
from shell.session_service.bootstrap.session.container.session_core_container import (
    SessionCoreContainer,
    configure_session_container,
)
from shell.session_service.framework.session.api.app import create_session_app
from shell.session_service.migrations.baseline import run_session_baseline

TEST_USER_ID = "session-test-user"
TEST_API_KEY = "test-api-key"
TEST_PRINCIPAL = Principal(subject_id=TEST_USER_ID, kind=PrincipalKind.USER)


async def make_session_app(tmp_path):
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'session-e2e.db'}"
    await run_session_baseline(db_url)
    container = SessionCoreContainer()
    container.config.db_url.from_value(db_url)
    configure_session_container(container)
    app = create_session_app(container)
    app.dependency_overrides[get_principal] = lambda: TEST_PRINCIPAL
    app.dependency_overrides[require_user_principal] = lambda: TEST_PRINCIPAL
    return app
