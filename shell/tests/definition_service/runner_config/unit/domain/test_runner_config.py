from __future__ import annotations

from datetime import UTC, datetime

from shell.definition_service.domain.definition.aggregates.runner_config.runner_config import (
    RunnerConfig,
)
from shell.definition_service.domain.definition.aggregates.runner_config.value_objects.runner_config_id import (
    RunnerConfigId,
)
from shell.platform.domain.value_objects.created_at import CreatedAt

_NOW = CreatedAt.from_datetime(datetime(2026, 6, 1, tzinfo=UTC))


class TestRunnerConfig:
    def test_new_creates_with_correct_fields(self) -> None:
        rc = RunnerConfig.create(
            id_=RunnerConfigId.generate(),
            now=_NOW,
        )
        assert rc.created_at == _NOW

    def test_fields_are_immutable(self) -> None:
        rc = RunnerConfig.create(
            id_=RunnerConfigId.generate(),
            now=_NOW,
        )
        assert rc.created_at == _NOW

    def test_identity_based_on_id(self) -> None:
        id1 = RunnerConfigId.generate()
        id2 = RunnerConfigId.generate()
        rc1 = RunnerConfig(id1, _NOW)
        rc2 = RunnerConfig(id1, _NOW)
        rc3 = RunnerConfig(id2, _NOW)
        assert rc1 == rc2
        assert rc1 != rc3
