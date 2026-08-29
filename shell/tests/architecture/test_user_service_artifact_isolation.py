"""Koncept: niezależny artefakt User BC.

Reguła: platforma i User BC są budowane jako odrębne pakiety bez kodu innych BC.

Poprawnie: wheels oraz Dockerfile zachowują granicę pilota User BC.
"""

from __future__ import annotations

import hashlib
import shutil
import zipfile
from pathlib import Path

from scripts.build_user_service_artifacts import build_artifacts

_FORBIDDEN_SERVICE_PACKAGES = (
    "shell/definition_service/",
    "shell/execution_service/",
    "shell/ingestion_service/",
    "shell/project_service/",
    "shell/scheduling_service/",
    "shell/session_service/",
)


def test_user_service_artifacts_contain_only_platform_and_user_service(
    tmp_path: Path,
) -> None:
    build_artifacts(tmp_path)

    platform_wheel = next(tmp_path.glob("shell_platform-*.whl"))
    user_wheel = next(tmp_path.glob("shell_user_service-*.whl"))

    with zipfile.ZipFile(platform_wheel) as archive:
        platform_files = set(archive.namelist())
    with zipfile.ZipFile(user_wheel) as archive:
        user_files = set(archive.namelist())

    assert any(path.startswith("shell/platform/") for path in platform_files)
    assert not any(path.startswith("shell/user_service/") for path in platform_files)
    assert any(path.startswith("shell/user_service/") for path in user_files)
    assert not any(path.startswith("shell/platform/") for path in user_files)
    assert "shell/user_service/bootstrap/user/config/default.yaml" in user_files
    assert "shell/user_service/bootstrap/user/config/prod.yaml" in user_files
    assert not any(
        path.startswith(forbidden)
        for path in platform_files | user_files
        for forbidden in _FORBIDDEN_SERVICE_PACKAGES
    )

    dockerfile = Path("shell/user_service/docker/Dockerfile").read_text(encoding="utf-8")

    assert "COPY shell/platform ./shell/platform" in dockerfile
    assert "COPY shell/user_service ./shell/user_service" in dockerfile
    assert "COPY shell/ ./shell/" not in dockerfile
    assert "pip install --no-cache-dir /tmp/wheels/*.whl" in dockerfile

    repository = tmp_path / "reproducibility-repository"
    (repository / "shell").mkdir(parents=True)
    shutil.copytree("shell/platform", repository / "shell/platform")
    shutil.copytree("shell/user_service", repository / "shell/user_service")
    shutil.copytree("packaging", repository / "packaging")

    first_output = tmp_path / "first"
    build_artifacts(first_output, repository)
    (repository / "shell/definition_service").mkdir(parents=True)
    (repository / "shell/definition_service/unrelated.py").write_text(
        "changed = True\n",
        encoding="utf-8",
    )
    second_output = tmp_path / "second"
    build_artifacts(second_output, repository)

    def artifact_hashes(output_dir: Path) -> dict[str, str]:
        return {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in output_dir.glob("*.whl")
        }

    assert artifact_hashes(first_output) == artifact_hashes(second_output)
