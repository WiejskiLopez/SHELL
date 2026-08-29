from __future__ import annotations

from shell.definition_service.bootstrap.definition.container.definition_core_container import (
    DefinitionCoreContainer,
    configure_definition_container,
)
from shell.definition_service.framework.definition.api.app import create_definition_app
from shell.definition_service.infrastructure.definition.seed import bootstrap_definition_database
from shell.tests.shared.sql_lifecycle import track_session_factory

TEST_API_KEY = "test-api-key"


async def make_definition_app(tmp_path):
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'definition-e2e.db'}"
    await bootstrap_definition_database(db_url)
    container = DefinitionCoreContainer()
    container.config.db_url.from_value(db_url)
    configure_definition_container(container)
    track_session_factory(container.session_factory())
    return create_definition_app(container)
