"""Koncept: niezależny artefakt Session BC.

Reguła: platforma i Session BC są budowane jako odrębne pakiety bez kodu innych BC.

Poprawnie: wheels oraz Dockerfile zachowują granicę pilota Session BC.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from scripts.build_user_service_artifacts import build_service_artifacts


def test_session_service_artifacts_are_isolated(tmp_path: Path) -> None:
    build_service_artifacts(
        service_name="session_service",
        service_package_name="shell-session-service",
        output_dir=tmp_path,
    )

    platform_wheel = next(tmp_path.glob("shell_platform-*.whl"))
    session_wheel = next(tmp_path.glob("shell_session_service-*.whl"))
    with zipfile.ZipFile(platform_wheel) as archive:
        platform_files = set(archive.namelist())
    with zipfile.ZipFile(session_wheel) as archive:
        session_files = set(archive.namelist())

    assert any(path.startswith("shell/platform/") for path in platform_files)
    assert not any(path.startswith("shell/session_service/") for path in platform_files)
    assert any(path.startswith("shell/session_service/") for path in session_files)
    assert not any(path.startswith("shell/user_service/") for path in session_files)
    assert "shell/session_service/migrations/versions/0001_session_baseline.py" in session_files

    dockerfile = Path("shell/session_service/docker/Dockerfile").read_text(encoding="utf-8")
    assert "COPY shell/platform ./shell/platform" in dockerfile
    assert "COPY shell/session_service ./shell/session_service" in dockerfile
    assert "COPY shell/ ./shell/" not in dockerfile
