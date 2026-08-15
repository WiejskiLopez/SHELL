from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.definition_service.domain.definition.aggregates.runner_config.runner_config import (
        RunnerConfig,
    )
    from shell.definition_service.infrastructure.definition.runner_config.persistence.sql.models import (
        RunnerConfigModel,
    )


def runner_config_update_model(model: RunnerConfigModel, entity: RunnerConfig) -> None:
    model.created_at = entity.created_at.value
