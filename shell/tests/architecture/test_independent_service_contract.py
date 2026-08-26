"""Koncept: wspólny kontrakt niezależnego mikroserwisu.

Reguła: każdy bounded context ma własny artefakt, konfigurację, obraz i migracje.

Poprawnie: wszystkie usługi spełniają ten sam automatycznie sprawdzany kontrakt.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


_BASE = Path(__file__).parents[3]
_SERVICES = (
    "definition_service",
    "execution_service",
    "ingestion_service",
    "project_service",
    "scheduling_service",
    "session_service",
    "user_service",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _assert_all(values: Iterable[bool], message: str) -> None:
    assert all(values), message


def test_every_service_has_an_independent_runtime_contract() -> None:
    for service_name in _SERVICES:
        service_root = _BASE / "shell" / service_name
        service_slug = service_name.removesuffix("_service")
        package_name = f"shell-{service_slug}-service"
        manifest = _BASE / "packaging" / package_name / "pyproject.toml"
        lockfile = manifest.with_name("uv.lock")
        dockerfile = service_root / "docker" / "Dockerfile"
        compose = service_root / "docker" / "docker-compose.yml"
        baseline = service_root / "migrations" / "baseline.py"
        revisions = service_root / "migrations" / "versions"
        config_root = service_root / "bootstrap" / service_slug / "config"

        assert manifest.is_file(), f"missing package manifest: {manifest}"
        assert lockfile.is_file(), f"missing service lockfile: {lockfile}"
        assert dockerfile.is_file(), f"missing service Dockerfile: {dockerfile}"
        assert compose.is_file(), f"missing service Compose file: {compose}"
        assert baseline.is_file(), f"missing migration runner: {baseline}"
        assert any(revisions.glob("*.py")), f"missing migration revision: {revisions}"
        _assert_all(
            ((config_root / filename).is_file() for filename in ("default.yaml", "prod.yaml")),
            f"missing owned configuration: {config_root}",
        )

        manifest_text = _read(manifest)
        dockerfile_text = _read(dockerfile)
        compose_text = _read(compose)
        baseline_text = _read(baseline)

        assert f'name = "{package_name}"' in manifest_text
        assert 'shell-platform>=' in manifest_text
        assert f'include = ["shell.{service_name}*"]' in manifest_text
        assert f"COPY shell/{service_name} ./shell/{service_name}" in dockerfile_text
        assert "COPY shell/ ./shell/" not in dockerfile_text
        assert "pip install --no-cache-dir /tmp/wheels/*.whl" in dockerfile_text
        assert f"{service_slug.upper()}_SERVICE_BROKER_URL" in compose_text
        assert f"{service_slug.upper()}_SERVICE_API_KEY" in compose_text
        assert "SHELL_EVENTS_BROKER_URL" not in compose_text
        assert "--db-url" not in compose_text
        assert "create_all" not in baseline_text

        source_text = "\n".join(_read(path) for path in service_root.rglob("*.py"))
        other_services = [name for name in _SERVICES if name != service_name]
        assert not any(
            re.search(rf"(?:from|import)\s+shell\.{other_service}(?:\.|\s)", source_text)
            for other_service in other_services
        ), f"{service_name} imports another bounded context"
