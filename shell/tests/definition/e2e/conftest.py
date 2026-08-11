from __future__ import annotations

from shell.definition.bootstrap.definition.container.definition_core_container import (
    DefinitionCoreContainer,
)
from shell.definition.framework.definition.api.app import create_definition_app
from shell.definition.infrastructure.definition.seed import _seed_base_definition_data
from shell.definition.migrations.baseline import run_definition_baseline

TEST_API_KEY = "test-api-key"


async def make_definition_app(tmp_path):
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'definition-e2e.db'}"
    await run_definition_baseline(db_url)
    await _seed_base_definition_data(db_url)
    container = DefinitionCoreContainer()
    container.config.db_url.from_value(db_url)
    return create_definition_app(container)