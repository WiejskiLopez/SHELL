"""Koncept: niezależny artefakt Session BC.

Reguła: platforma i Session BC są budowane jako odrębne pakiety bez kodu innych BC.

Poprawnie: wheels oraz Dockerfile zachowują granicę pilota Session BC.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wheel_helpers import ServiceWheels


def test_session_service_artifacts_are_isolated(
    artifact_services: dict[str, ServiceWheels],
) -> None:
    wheels = artifact_services["session_service"]
    with zipfile.ZipFile(wheels.platform_wheel) as archive:
        platform_files = set(archive.namelist())
    with zipfile.ZipFile(wheels.service_wheel) as archive:
        session_files = set(archive.namelist())

    assert any(path.startswith("shell/platform/") for path in platform_files)
    assert not any(path.startswith("shell/session_service/") for path in platform_files)
    assert any(path.startswith("shell/session_service/") for path in session_files)
    assert not any(path.startswith("shell/user_service/") for path in session_files)
    assert "shell/session_service/migrations/versions/session_0001_session.py" in session_files

    dockerfile = Path("shell/session_service/docker/Dockerfile").read_text(encoding="utf-8")
    assert "COPY shell/platform ./shell/platform" in dockerfile
    assert "COPY shell/session_service ./shell/session_service" in dockerfile
    assert "COPY shell/ ./shell/" not in dockerfile
