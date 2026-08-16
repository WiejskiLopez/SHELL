from __future__ import annotations

from shell.session_service.infrastructure.session.seed import seed_session_dev_data
from shell.session_service.infrastructure.session.session.persistence.sql.models.session import (
    SessionModel,
)
from shell.tests.shared.seed import count_rows


async def test_seed_dev_data_is_idempotent(tmp_path) -> None:
    url = f"sqlite+aiosqlite:///{tmp_path / 'seed.db'}"
    await seed_session_dev_data(url)
    first_count = await count_rows(url, SessionModel)
    assert first_count > 0
    await seed_session_dev_data(url)
    second_count = await count_rows(url, SessionModel)
    assert second_count == first_count
