from shell.domain.definition.aggregates.runner_config.runner_config import RunnerConfig
from shell.domain.definition.aggregates.runner_config.value_objects.runner_config_id import (
    RunnerConfigId,
)
from shell.infrastructure.definition.runner_config.persistence.sql.models import (
    RunnerConfigModel,
)
from shell.platform.domain.value_objects.created_at import CreatedAt


def runner_config_model_to_entity(runner_config_model: RunnerConfigModel) -> RunnerConfig:
    return RunnerConfig.restore(
        id=RunnerConfigId(runner_config_model.id),
        created_at=CreatedAt.from_datetime(runner_config_model.created_at),
    )

