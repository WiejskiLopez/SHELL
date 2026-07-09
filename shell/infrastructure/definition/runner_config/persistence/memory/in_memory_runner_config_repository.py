from __future__ import annotations

from shell.domain.definition.aggregates.runner_config.repositories.runner_config_repository import (
    RunnerConfigRepository,
)
from shell.domain.definition.aggregates.runner_config.runner_config import RunnerConfig
from shell.domain.definition.aggregates.runner_config.value_objects.runner_config_id import (
    RunnerConfigId,
)
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository


class InMemoryRunnerConfigRepository(
    InMemoryRepository[RunnerConfig, RunnerConfigId], RunnerConfigRepository
):
    pass
