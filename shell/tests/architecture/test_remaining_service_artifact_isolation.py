"""Koncept: niezależne artefakty pięciu pozostałych BC.

Reguła: każdy artefakt zawiera wyłącznie platformę i własny bounded context.

Poprawnie: wheels są budowane niezależnie, bez kodu pozostałych usług.
"""

from __future__ import annotations

import zipfile
from typing import TYPE_CHECKING

from scripts.build_user_service_artifacts import build_service_artifacts

if TYPE_CHECKING:
    from pathlib import Path

_SERVICES = (
    ("definition_service", "shell-definition-service"),
    ("execution_service", "shell-execution-service"),
    ("ingestion_service", "shell-ingestion-service"),
    ("project_service", "shell-project-service"),
    ("scheduling_service", "shell-scheduling-service"),
)


def test_remaining_service_artifacts_are_isolated(tmp_path: Path) -> None:
    for service_name, package_name in _SERVICES:
        output_dir = tmp_path / service_name
        build_service_artifacts(
            service_name=service_name,
            service_package_name=package_name,
            output_dir=output_dir,
        )
        platform_wheel = next(output_dir.glob("shell_platform-*.whl"))
        service_wheel = next(output_dir.glob(f"{package_name.replace('-', '_')}-*.whl"))
        with zipfile.ZipFile(platform_wheel) as archive:
            platform_files = set(archive.namelist())
        with zipfile.ZipFile(service_wheel) as archive:
            service_files = set(archive.namelist())

        assert any(path.startswith("shell/platform/") for path in platform_files)
        assert not any(path.startswith(f"shell/{service_name}/") for path in platform_files)
        assert any(path.startswith(f"shell/{service_name}/") for path in service_files)
        assert not any(path.startswith("shell/platform/") for path in service_files)
        assert f"shell/{service_name}/migrations/script.py.mako" in service_files
        assert not any(
            path.startswith(f"shell/{other_name}/")
            for other_name, _ in _SERVICES
            if other_name != service_name
            for path in service_files
        )
