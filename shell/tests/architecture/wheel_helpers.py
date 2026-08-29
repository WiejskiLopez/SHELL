"""Shared wheel-artifact helpers for the artifact-isolation architecture tests.

Artifacts are built once per session and consumed by every test, instead of
each test invoking ``uv build`` from scratch (~30 runs before; ~1 run now).
"""

from __future__ import annotations

import pathlib
import shutil
from dataclasses import dataclass
from typing import TYPE_CHECKING

from scripts.build_user_service_artifacts import build_single_wheel

if TYPE_CHECKING:
    from pathlib import Path

THIS_DIR = pathlib.Path(__file__).resolve().parent
REPOSITORY_ROOT = THIS_DIR.parents[2]  # repo root

SERVICES = (
    ("definition_service", "shell-definition-service"),
    ("execution_service", "shell-execution-service"),
    ("ingestion_service", "shell-ingestion-service"),
    ("project_service", "shell-project-service"),
    ("scheduling_service", "shell-scheduling-service"),
    ("session_service", "shell-session-service"),
    ("user_service", "shell-user-service"),
)


@dataclass(frozen=True)
class ServiceWheels:
    """Paths to the once-built platform and bounded-context wheels."""

    output_dir: Path
    platform_wheel: Path
    service_wheel: Path


def build_service_wheels(build_root: Path) -> dict[str, ServiceWheels]:
    """Build the platform wheel once and each bounded-context wheel once.

    Each service directory receives a copy of the platform wheel so a single
    directory holds both artifacts (the layout ``uv build`` produces today).
    """
    platform_dir = build_root / "platform"
    build_single_wheel(
        package_name="shell-platform",
        manifest_path=REPOSITORY_ROOT / "packaging" / "shell-platform" / "pyproject.toml",
        source_path=REPOSITORY_ROOT / "shell" / "platform",
        output_dir=platform_dir,
    )
    platform_wheel = next(platform_dir.glob("shell_platform-*.whl"))
    result: dict[str, ServiceWheels] = {}
    for service_name, package_name in SERVICES:
        service_dir = build_root / service_name
        build_single_wheel(
            package_name=package_name,
            manifest_path=REPOSITORY_ROOT / "packaging" / package_name / "pyproject.toml",
            source_path=REPOSITORY_ROOT / "shell" / service_name,
            output_dir=service_dir,
        )
        service_wheel_name = f"{package_name.replace('-', '_')}-*.whl"
        service_wheel = next(service_dir.glob(service_wheel_name))
        shutil.copy2(platform_wheel, service_dir / platform_wheel.name)
        result[service_name] = ServiceWheels(
            output_dir=service_dir,
            platform_wheel=service_dir / platform_wheel.name,
            service_wheel=service_wheel,
        )
    return result
