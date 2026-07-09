from shell.domain.definition.aggregates.runner_config.runner_config import RunnerConfig
from shell.domain.definition.aggregates.runner_config.value_objects.runner_config_id import (
    RunnerConfigId,
)
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.infrastructure.definition.runner_config.persistence.sql.models import (
    RunnerConfigModel,
)


def runner_config_model_to_entity(runner_config_model: RunnerConfigModel) -> RunnerConfig:
    return RunnerConfig(
        id=RunnerConfigId(runner_config_model.id),
        created_at=CreatedAt.from_datetime(runner_config_model.created_at),
    )


def runner_config_entity_to_model(runner_config: RunnerConfig) -> RunnerConfigModel:
    return RunnerConfigModel(
        id=runner_config.id.value,
        created_at=runner_config.created_at.value,
    )


def runner_config_update_model(model: RunnerConfigModel, entity: RunnerConfig) -> None:
    model.created_at = entity.created_at.value
