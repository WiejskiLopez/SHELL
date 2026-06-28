from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.definition.entities.runner_config import RunnerConfig
from shell.domain.definition.value_objects.created_at import CreatedAt
from shell.domain.definition.value_objects.ids import RunnerConfigId
from shell.domain.definition.value_objects.package_name import PackageName
from shell.domain.definition.value_objects.runner_body import RunnerBody
from shell.domain.definition.value_objects.runner_kind import RunnerKind
from shell.domain.platform.value_objects.hash import Hash

_NOW = datetime(2026, 6, 1, tzinfo=UTC)


class TestRunnerConfig:
    def test_new_creates_with_correct_fields(self) -> None:
        rc = RunnerConfig.new(
            id_=RunnerConfigId.generate(),
            package_name=PackageName("shell-runners"),
            kind=RunnerKind("node"),
            body=RunnerBody({"timeout": 30, "retries": 3}),
            config_hash=Hash.of('{"timeout":30}'),
            now=CreatedAt(_NOW),
        )
        assert rc.package_name == PackageName("shell-runners")
        assert rc.kind == RunnerKind("node")
        assert rc.body == RunnerBody({"timeout": 30, "retries": 3})
        assert rc.created_at == CreatedAt(_NOW)

    def test_fields_are_immutable(self) -> None:
        rc = RunnerConfig.new(
            id_=RunnerConfigId.generate(),
            package_name=PackageName("pkg"),
            kind=RunnerKind("node"),
            body=RunnerBody({}),
            config_hash=Hash.of("x"),
            now=CreatedAt(_NOW),
        )
        assert rc.package_name == PackageName("pkg")
        assert rc.kind == RunnerKind("node")

    def test_identity_based_on_id(self) -> None:
        id1 = RunnerConfigId.generate()
        id2 = RunnerConfigId.generate()
        rc1 = RunnerConfig(id1, PackageName("a"), RunnerKind("k1"), Hash.of("x"), RunnerBody({}), CreatedAt(_NOW))
        rc2 = RunnerConfig(id1, PackageName("b"), RunnerKind("k2"), Hash.of("y"), RunnerBody({"z": 1}), CreatedAt(_NOW))
        rc3 = RunnerConfig(id2, PackageName("a"), RunnerKind("k1"), Hash.of("x"), RunnerBody({}), CreatedAt(_NOW))
        assert rc1 == rc2
        assert rc1 != rc3
