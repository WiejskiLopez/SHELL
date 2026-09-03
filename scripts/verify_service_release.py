#!/usr/bin/env python
"""Verify a local, reproducible release candidate for one SHELL service."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import shutil
import subprocess
import tarfile
import tempfile
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.build_user_service_artifacts import build_service_artifacts
from scripts.verify_user_service_image import verify_image

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _run(*arguments: str, cwd: Path = REPOSITORY_ROOT) -> str:
    result = subprocess.run(
        list(arguments),
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def _package_metadata(package_name: str) -> dict[str, Any]:
    manifest = REPOSITORY_ROOT / "packaging" / package_name / "pyproject.toml"
    with manifest.open("rb") as stream:
        return tomllib.load(stream)


def _migration_head(service_name: str) -> str:
    """Return the single head revision of the service's Alembic chain."""

    versions_dir = REPOSITORY_ROOT / "shell" / service_name / "migrations" / "versions"
    revisions: set[str] = set()
    referenced: set[str] = set()
    for path in versions_dir.glob("*.py"):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        revision: str | None = None
        down_revision: str | None = None
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if (
                    not isinstance(target, ast.Name)
                    or not isinstance(node.value, ast.Constant)
                    or not isinstance(node.value.value, str)
                ):
                    continue
                if target.id == "revision":
                    revision = node.value.value
                elif target.id == "down_revision":
                    down_revision = node.value.value
        if revision is None:
            raise RuntimeError(f"Missing revision in {path}")
        revisions.add(revision)
        if down_revision is not None:
            referenced.add(down_revision)
    heads = sorted(revisions - referenced)
    if len(heads) != 1:
        raise RuntimeError(f"Expected a single migration head for {service_name}, got {heads!r}")
    return heads[0]


def _require_clean_tree() -> None:
    status = _run("git", "status", "--porcelain")
    if status:
        raise RuntimeError("Release requires a clean working tree")


def _verify_lockfile(package_name: str) -> None:
    package_root = REPOSITORY_ROOT / "packaging" / package_name
    if not (package_root / "uv.lock").is_file():
        raise RuntimeError(f"Missing lockfile for {package_name}")
    with tempfile.TemporaryDirectory(prefix="shell-release-lock-") as temporary_dir:
        isolated_root = Path(temporary_dir)
        platform_copy = isolated_root / "shell-platform"
        service_copy = isolated_root / package_name
        shutil.copytree(REPOSITORY_ROOT / "packaging" / "shell-platform", platform_copy)
        shutil.copytree(package_root, service_copy)
        _run("uv", "lock", "--check", cwd=service_copy)


def _image_id(image: str) -> str:
    return _run("docker", "image", "inspect", image, "--format", "{{.Id}}")


def _build_image(service_name: str, image: str) -> str:
    dockerfile = REPOSITORY_ROOT / "shell" / service_name / "docker" / "Dockerfile"
    _run("docker", "build", "--file", str(dockerfile), "--tag", image, ".")
    return _image_id(image)


def _filesystem_digest(image: str) -> str:
    with tempfile.NamedTemporaryFile(suffix=".tar", delete=False) as archive_file:
        archive_path = Path(archive_file.name)
    container = _run("docker", "create", image)
    try:
        _run("docker", "export", container, "--output", str(archive_path))
        digest = hashlib.sha256()
        with tarfile.open(archive_path) as archive:
            for member in sorted(archive.getmembers(), key=lambda item: item.name):
                digest.update(member.name.encode("utf-8"))
                member_type = (
                    member.type.decode("ascii")
                    if isinstance(member.type, bytes)
                    else str(member.type)
                )
                digest.update(f"{member_type}:{member.mode}:{member.size}".encode("ascii"))
                if member.isfile():
                    content = archive.extractfile(member)
                    if content is not None:
                        while chunk := content.read(1024 * 1024):
                            digest.update(chunk)
        return digest.hexdigest()
    finally:
        subprocess.run(["docker", "rm", container], check=False, capture_output=True)
        archive_path.unlink(missing_ok=True)


def _verify_unrelated_service_does_not_change_image(
    *,
    service_name: str,
    package_name: str,
) -> str:
    with tempfile.TemporaryDirectory(prefix="shell-release-context-") as temporary_dir:
        isolated_root = Path(temporary_dir)
        (isolated_root / "shell").mkdir()
        shutil.copytree(
            REPOSITORY_ROOT / "shell" / "platform", isolated_root / "shell" / "platform"
        )
        shutil.copytree(
            REPOSITORY_ROOT / "shell" / service_name,
            isolated_root / "shell" / service_name,
        )
        shutil.copytree(REPOSITORY_ROOT / "packaging", isolated_root / "packaging")
        dockerfile = isolated_root / "shell" / service_name / "docker" / "Dockerfile"
        first_image = "shell-release-independence-before"
        second_image = "shell-release-independence-after"
        try:
            _run(
                "docker",
                "build",
                "--file",
                str(dockerfile),
                "--tag",
                first_image,
                str(isolated_root),
            )
            first_digest = _filesystem_digest(first_image)
            unrelated_service = (
                "definition_service"
                if service_name != "definition_service"
                else "execution_service"
            )
            unrelated_file = isolated_root / "shell" / unrelated_service / "unrelated.py"
            unrelated_file.parent.mkdir(parents=True)
            unrelated_file.write_text("changed = True\n", encoding="utf-8")
            _run(
                "docker",
                "build",
                "--file",
                str(dockerfile),
                "--tag",
                second_image,
                str(isolated_root),
            )
            second_digest = _filesystem_digest(second_image)
            if first_digest != second_digest:
                raise RuntimeError(
                    f"{service_name} image filesystem digest changed after an unrelated BC change"
                )
            return first_digest
        finally:
            subprocess.run(
                ["docker", "rmi", "--force", first_image, second_image],
                check=False,
                capture_output=True,
            )


def build_release_manifest(
    *,
    service_name: str,
    package_name: str,
    image: str,
    output_path: Path,
    allow_dirty: bool = False,
    dry_run: bool = False,
    artifacts_dir: Path | None = None,
) -> dict[str, Any]:
    if not allow_dirty:
        _require_clean_tree()
    metadata = _package_metadata(package_name)
    version = str(metadata["project"]["version"])
    commit = _run("git", "rev-parse", "HEAD")
    _verify_lockfile(package_name)

    if artifacts_dir is None:
        with tempfile.TemporaryDirectory(prefix="shell-release-artifacts-") as temporary_dir:
            artifact_dir = Path(temporary_dir)
            build_service_artifacts(
                service_name=service_name,
                service_package_name=package_name,
                output_dir=artifact_dir,
            )
            artifact_hashes = {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in artifact_dir.glob("*.whl")
            }
    else:
        artifact_hashes = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in artifacts_dir.glob("*.whl")
        }

    image_id = None if dry_run else _build_image(service_name, image)
    if image_id is not None:
        verify_image(image, service_name.removesuffix("_service"))
    independence_digest = (
        None
        if dry_run
        else _verify_unrelated_service_does_not_change_image(
            service_name=service_name,
            package_name=package_name,
        )
    )
    manifest: dict[str, Any] = {
        "service": package_name,
        "version": version,
        "commit": commit,
        "source_status": "dirty" if allow_dirty else "clean",
        "image": image,
        "image_id": image_id,
        "image_digest": image_id,
        "image_digest_type": "local-image-id" if image_id else None,
        "independence_filesystem_digest": independence_digest,
        "platform_version": str(_package_metadata("shell-platform")["project"]["version"]),
        "migration_head": _migration_head(service_name),
        "artifact_sha256": artifact_hashes,
        "verified_at": datetime.now(UTC).isoformat(),
        "status": "candidate" if allow_dirty else "verified",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--service",
        choices=(
            "definition_service",
            "execution_service",
            "ingestion_service",
            "project_service",
            "scheduling_service",
            "session_service",
            "user_service",
        ),
        default="user_service",
    )
    parser.add_argument("--package", default=None)
    parser.add_argument("--image", default=None)
    parser.add_argument(
        "--output",
        type=Path,
        default=REPOSITORY_ROOT / "dist" / "user-service" / "release-manifest.json",
    )
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    service_package = args.package or f"shell-{args.service.removesuffix('_service')}-service"
    service_image = (
        args.image or f"shell-{args.service.removesuffix('_service')}-service:release-candidate"
    )
    build_release_manifest(
        service_name=args.service,
        package_name=service_package,
        image=service_image,
        output_path=args.output.resolve(),
        allow_dirty=args.allow_dirty,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
