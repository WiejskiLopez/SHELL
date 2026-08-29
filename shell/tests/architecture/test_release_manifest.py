"""Koncept: kontrolowany manifest release mikroserwisu.

Reguła: manifest zawiera wersję, commit, status źródła, platformę i sumy artefaktów.

Poprawnie: verifier generuje kompletny manifest bez publikowania obrazu.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from scripts.verify_service_release import build_release_manifest

if TYPE_CHECKING:
    from pathlib import Path

    from wheel_helpers import ServiceWheels

_SERVICES = (
    "definition_service",
    "execution_service",
    "ingestion_service",
    "project_service",
    "scheduling_service",
    "session_service",
    "user_service",
)


def test_release_manifest_contains_verified_metadata(
    artifact_services: dict[str, ServiceWheels],
    tmp_path: Path,
) -> None:
    for service_name in _SERVICES:
        service_slug = service_name.removesuffix("_service")
        package_name = f"shell-{service_slug}-service"
        output_path = tmp_path / service_name / "release-manifest.json"
        manifest = build_release_manifest(
            service_name=service_name,
            package_name=package_name,
            image=f"{package_name}:test-manifest",
            output_path=output_path,
            allow_dirty=True,
            dry_run=True,
            artifacts_dir=artifact_services[service_name].output_dir,
        )

        assert output_path.is_file()
        assert json.loads(output_path.read_text(encoding="utf-8")) == manifest
        assert manifest["service"] == package_name
        assert manifest["version"] == "0.1.0"
        assert len(manifest["commit"]) == 40
        assert manifest["source_status"] == "dirty"
        assert manifest["status"] == "candidate"
        assert manifest["platform_version"] == "0.1.0"
        assert manifest["image_id"] is None
        assert manifest["image_digest"] is None
        assert set(manifest["artifact_sha256"]) == {
            "shell_platform-0.1.0-py3-none-any.whl",
            f"{package_name.replace('-', '_')}-0.1.0-py3-none-any.whl",
        }
        assert manifest["migration_head"] == f"0001_{service_slug}_baseline"
