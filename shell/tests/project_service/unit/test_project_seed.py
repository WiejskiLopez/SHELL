from __future__ import annotations

from shell.project_service.infrastructure.project.project.persistence.sql.models.project import (
    ProjectModel,
)
from shell.project_service.infrastructure.project.seed import seed_project_dev_data
from shell.tests.shared.seed import count_rows


async def test_seed_dev_data_is_idempotent(tmp_path) -> None:
    url = f"sqlite+aiosqlite:///{tmp_path / 'seed.db'}"
    await seed_project_dev_data(url)
    first_count = await count_rows(url, ProjectModel)
    assert first_count > 0
    await seed_project_dev_data(url)
    second_count = await count_rows(url, ProjectModel)
    assert second_count == first_count
