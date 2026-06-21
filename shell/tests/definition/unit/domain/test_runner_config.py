from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.definition.entities.runner_config import RunnerConfig
from shell.domain.definition.value_objects.ids import RunnerConfigId
from shell.domain.platform.value_objects.hash import Hash

_NOW = datetime(2026, 6, 1, tzinfo=UTC)


class TestRunnerConfig:
    def test_new_creates_with_correct_fields(self) -> None:
        rc = RunnerConfig.new(
            id_=RunnerConfigId.generate(),
            package_name="shell-runners",
            kind="node",
            body={"timeout": 30, "retries": 3},
            config_hash=Hash.of('{"timeout":30}'),
            now=_NOW,
        )
        assert rc.package_name == "shell-runners"
        assert rc.kind == "node"
        assert rc.body == {"timeout": 30, "retries": 3}
        assert rc.created_at == _NOW

    def test_fields_are_immutable(self) -> None:
        rc = RunnerConfig.new(
            id_=RunnerConfigId.generate(),
            package_name="pkg",
            kind="node",
            body={},
            config_hash=Hash.of("x"),
            now=_NOW,
        )
        assert rc.package_name == "pkg"
        assert rc.kind == "node"

    def test_identity_based_on_id(self) -> None:
        id1 = RunnerConfigId.generate()
        id2 = RunnerConfigId.generate()
        rc1 = RunnerConfig(id1, "a", "k1", Hash.of("x"), {}, _NOW)
        rc2 = RunnerConfig(id1, "b", "k2", Hash.of("y"), {"z": 1}, _NOW)
        rc3 = RunnerConfig(id2, "a", "k1", Hash.of("x"), {}, _NOW)
        assert rc1 == rc2
        assert rc1 != rc3
