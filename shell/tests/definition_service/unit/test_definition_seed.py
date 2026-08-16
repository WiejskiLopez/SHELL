from __future__ import annotations

from shell.definition_service.infrastructure.definition.graph_definition.persistence.sql.models.graph_definition import (
    GraphDefinitionModel,
)
from shell.definition_service.infrastructure.definition.seed import seed_definition_dev_data
from shell.tests.shared.seed import count_rows


async def test_seed_dev_data_is_idempotent(tmp_path) -> None:
    url = f"sqlite+aiosqlite:///{tmp_path / 'seed.db'}"
    await seed_definition_dev_data(url)
    first_count = await count_rows(url, GraphDefinitionModel)
    assert first_count > 0
    await seed_definition_dev_data(url)
    second_count = await count_rows(url, GraphDefinitionModel)
    assert second_count == first_count
