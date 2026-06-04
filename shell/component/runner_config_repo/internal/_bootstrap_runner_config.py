from __future__ import annotations

from shell.utils.path.path import Path, PathType


def _bootstrap_runner_config(
    repo,
    package_name: str,
    kind: str,
    yaml_path: PathType,
) -> str:
    if Path.is_file(yaml_path):
        body = Path.read_text(yaml_path)
        repo.import_runner_config_if_changed(
            package_name=package_name,
            kind=kind,
            body=body,
            source_uri=str(yaml_path),
        )
        return body
    row = repo.get_current_runner_config(package_name=package_name, kind=kind)
    if row is None:
        raise RuntimeError(
            f"runner_config not found in DB for package='{package_name}' kind='{kind}' "
            f"and seed file '{yaml_path}' does not exist"
        )
    return row["body_yaml_raw"]


def _get_runner_config_body(repo, package_name: str, kind: str) -> str:
    row = repo.get_current_runner_config(package_name=package_name, kind=kind)
    if row is None:
        raise RuntimeError(
            f"runner_config not found in DB for package='{package_name}' kind='{kind}'"
        )
    return row["body_yaml_raw"]
