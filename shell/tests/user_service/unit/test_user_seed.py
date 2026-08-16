from __future__ import annotations

from shell.tests.shared.seed import count_rows
from shell.user_service.infrastructure.user.seed import seed_user_dev_data
from shell.user_service.infrastructure.user.user.persistence.sql.models.user import UserModel


async def test_seed_dev_data_is_idempotent(tmp_path) -> None:
    url = f"sqlite+aiosqlite:///{tmp_path / 'seed.db'}"
    await seed_user_dev_data(url)
    first_count = await count_rows(url, UserModel)
    assert first_count > 0
    await seed_user_dev_data(url)
    second_count = await count_rows(url, UserModel)
    assert second_count == first_count
