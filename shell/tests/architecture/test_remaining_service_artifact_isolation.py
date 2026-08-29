"""Koncept: niezależne artefakty pięciu pozostałych BC.

Reguła: każdy artefakt zawiera wyłącznie platformę i własny bounded context.

Poprawnie: wheels są budowane niezależnie, bez kodu pozostałych usług.
"""

from __future__ import annotations

import zipfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wheel_helpers import ServiceWheels

import pytest

_SERVICES = (
    "definition_service",
    "execution_service",
    "ingestion_service",
    "project_service",
    "scheduling_service",
)


def test_remaining_service_artifacts_are_isolated(
    artifact_services: dict[str, ServiceWheels],
) -> None:
    for service_name in _SERVICES:
        wheels = artifact_services[service_name]
        with zipfile.ZipFile(wheels.platform_wheel) as archive:
            platform_files = set(archive.namelist())
        with zipfile.ZipFile(wheels.service_wheel) as archive:
            service_files = set(archive.namelist())

        assert any(path.startswith("shell/platform/") for path in platform_files)
        assert not any(path.startswith(f"shell/{service_name}/") for path in platform_files)
        assert any(path.startswith(f"shell/{service_name}/") for path in service_files)
        assert not any(path.startswith("shell/platform/") for path in service_files)
        assert f"shell/{service_name}/migrations/script.py.mako" in service_files
        assert not any(
            path.startswith(f"shell/{other_name}/")
            for other_name in _SERVICES
            if other_name != service_name
            for path in service_files
        )


@pytest.fixture(autouse=True)
def _require_shared_wheels(artifact_services: dict[str, ServiceWheels]) -> None:
    """Fail loudly if the shared wheel cache is empty (misconfiguration)."""
    assert artifact_services, "artifact_services must be built for isolation tests"
