from __future__ import annotations

from shell.ingestion_service.infrastructure.ingestion.persistence.sql.models.base import (
    OutboxEventModel,
)
from shell.ingestion_service.infrastructure.ingestion.seed import seed_ingestion_dev_data
from shell.tests.shared.seed import count_rows


async def test_seed_dev_data_is_idempotent(tmp_path) -> None:
    url = f"sqlite+aiosqlite:///{tmp_path / 'seed.db'}"
    await seed_ingestion_dev_data(url)
    first_count = await count_rows(url, OutboxEventModel)
    assert first_count > 0
    await seed_ingestion_dev_data(url)
    second_count = await count_rows(url, OutboxEventModel)
    assert second_count == first_count
