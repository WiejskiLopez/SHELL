from __future__ import annotations

from shell.scheduling_service.infrastructure.scheduling.scheduler_definition.persistence.sql.models.scheduler_definition import (
    SchedulerDefinitionModel,
)
from shell.scheduling_service.infrastructure.scheduling.seed import seed_scheduling_dev_data
from shell.tests.shared.seed import count_rows


async def test_seed_dev_data_is_idempotent(tmp_path) -> None:
    url = f"sqlite+aiosqlite:///{tmp_path / 'seed.db'}"
    await seed_scheduling_dev_data(url)
    first_count = await count_rows(url, SchedulerDefinitionModel)
    assert first_count > 0
    await seed_scheduling_dev_data(url)
    second_count = await count_rows(url, SchedulerDefinitionModel)
    assert second_count == first_count
