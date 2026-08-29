#!/usr/bin/env python
"""Build the independent platform and User BC wheels from isolated source trees."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _stage_package(
    *,
    package_name: str,
    manifest_path: Path,
    source_path: Path,
    stage_root: Path,
) -> Path:
    stage_path = stage_root / package_name
    (stage_path / "shell").mkdir(parents=True)
    shutil.copy2(manifest_path, stage_path / "pyproject.toml")
    shutil.copytree(source_path, stage_path / "shell" / source_path.name)
    return stage_path


def build_artifacts(output_dir: Path, repository_root: Path = REPOSITORY_ROOT) -> None:
    """Build the User BC artifacts for backward-compatible callers."""
    build_service_artifacts(
        service_name="user_service",
        service_package_name="shell-user-service",
        output_dir=output_dir,
        repository_root=repository_root,
    )


def build_single_wheel(
    *,
    package_name: str,
    manifest_path: Path,
    source_path: Path,
    output_dir: Path,
) -> None:
    """Build one isolated wheel for a package (platform or a bounded context).

    Extracted from :func:`build_service_artifacts` so callers can build and
    cache a single artifact without re-packaging the platform source each time.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="shell-package-build-") as temporary_dir:
        package_stage = _stage_package(
            package_name=package_name,
            manifest_path=manifest_path,
            source_path=source_path,
            stage_root=Path(temporary_dir),
        )
        build_environment = os.environ.copy()
        build_environment["SOURCE_DATE_EPOCH"] = "0"
        subprocess.run(
            ["uv", "build", "--wheel", "--out-dir", str(output_dir)],
            cwd=package_stage,
            check=True,
            env=build_environment,
        )


def build_service_artifacts(
    *,
    service_name: str,
    service_package_name: str,
    output_dir: Path,
    repository_root: Path = REPOSITORY_ROOT,
) -> None:
    """Build a platform wheel and one bounded-context wheel in isolation."""
    output_dir.mkdir(parents=True, exist_ok=True)
    repository_root = repository_root.resolve()
    build_single_wheel(
        package_name="shell-platform",
        manifest_path=repository_root / "packaging" / "shell-platform" / "pyproject.toml",
        source_path=repository_root / "shell" / "platform",
        output_dir=output_dir,
    )
    build_single_wheel(
        package_name=service_package_name,
        manifest_path=repository_root / "packaging" / service_package_name / "pyproject.toml",
        source_path=repository_root / "shell" / service_name,
        output_dir=output_dir,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPOSITORY_ROOT / "dist" / "user-service",
    )
    args = parser.parse_args()
    build_artifacts(args.output_dir.resolve())


if __name__ == "__main__":
    main()
