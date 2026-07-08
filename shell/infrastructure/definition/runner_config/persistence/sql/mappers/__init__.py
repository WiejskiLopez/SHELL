from shell.domain.definition.entities.runner_config import RunnerConfig
from shell.domain.definition.value_objects.ids import RunnerConfigId
from shell.domain.definition.value_objects.package_name import PackageName
from shell.domain.definition.value_objects.runner_body import RunnerBody
from shell.domain.definition.value_objects.runner_kind import RunnerKind
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.hash import Hash
from shell.infrastructure.definition.runner_config.persistence.sql.models import (
    RunnerConfigModel,
)


def runner_config_model_to_entity(runner_config_model: RunnerConfigModel) -> RunnerConfig:
    return RunnerConfig(
        id=RunnerConfigId(runner_config_model.id),
        package_name=PackageName(runner_config_model.package_name),
        kind=RunnerKind(runner_config_model.kind),
        hash=Hash(runner_config_model.hash),
        body=RunnerBody(dict(runner_config_model.body)),
        created_at=CreatedAt.from_datetime(runner_config_model.created_at),
    )


def runner_config_entity_to_model(runner_config: RunnerConfig) -> RunnerConfigModel:
    return RunnerConfigModel(
        id=runner_config.id.value,
        package_name=str(runner_config.package_name),
        kind=str(runner_config.kind),
        hash=runner_config.hash.value,
        body=runner_config.body.value,
        created_at=runner_config.created_at.value,
    )


def runner_config_update_model(model: RunnerConfigModel, entity: RunnerConfig) -> None:
    model.package_name = str(entity.package_name)
    model.kind = str(entity.kind)
    model.hash = entity.hash.value
    model.body = entity.body.value
    model.created_at = entity.created_at.value
