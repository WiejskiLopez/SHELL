from __future__ import annotations

from typing import TYPE_CHECKING

from shell.infrastructure.definition.runner_config.persistence.sql.models import (
    RunnerConfigModel,
)

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.runner_config.runner_config import RunnerConfig


def runner_config_entity_to_model(runner_config: RunnerConfig) -> RunnerConfigModel:
    return RunnerConfigModel(
        id=runner_config.id.value,
        created_at=runner_config.created_at.value,
    )
