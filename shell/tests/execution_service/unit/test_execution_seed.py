from __future__ import annotations

from shell.execution_service.infrastructure.execution.seed import seed_execution_dev_data
from shell.execution_service.infrastructure.execution.workflow.persistence.sql.models.workflow import (
    WorkflowModel,
)
from shell.tests.shared.seed import count_rows


async def test_seed_dev_data_is_idempotent(tmp_path) -> None:
    url = f"sqlite+aiosqlite:///{tmp_path / 'seed.db'}"
    await seed_execution_dev_data(url)
    first_count = await count_rows(url, WorkflowModel)
    assert first_count > 0
    await seed_execution_dev_data(url)
    second_count = await count_rows(url, WorkflowModel)
    assert second_count == first_count
