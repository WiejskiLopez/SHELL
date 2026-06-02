"""manifest.py
Manifest: structured representation of the module's manifest.

Manifest body is sourced exclusively from runner_config DB (kind='manifest').
The original manifest.yaml file is used only as a one-time bootstrap seed.

Fields:
    _app                — parent App (DOM back-reference)
    _manifest_file_body — raw YAML text of the manifest, loaded from DB
"""

from __future__ import annotations

from shell.component.manifest.internal._manifest_name import get_manifest_name
from shell.component.manifest.internal._manifest_version import get_manifest_version
from shell.component.manifest.internal._manifest_description import get_manifest_description
from shell.component.manifest.internal._assert_manifest_body_loaded import _assert_manifest_body_loaded
from shell.component.manifest.internal._assert_manifest_not_empty import _assert_manifest_not_empty
from shell.constants.constants import MANIFEST_YAML


class Manifest:
    """Holds raw manifest YAML body for the running module, sourced from DB."""

    __slots__ = ("_app", "_manifest_file_body")

    def __init__(self, app=None) -> None:
        self._app = app
        self._manifest_file_body: str = ""

    @property
    def manifest_file_body_(self) -> str:
        """Return manifest YAML text. Raises if empty (init_manifest not called)."""
        _assert_manifest_body_loaded(self._manifest_file_body)
        return self._manifest_file_body

    @property
    def manifest_name_(self) -> str:
        return get_manifest_name(self._app)

    @property
    def manifest_version_(self) -> str:
        return get_manifest_version(self._app)

    @property
    def manifest_description_(self) -> str:
        return get_manifest_description(self._app)

    def init_manifest(self) -> None:
        runner_root_dir = self._app.cli_.cli_properties_.runner_root_dir_
        package_name = runner_root_dir.name
        seed_path = runner_root_dir / MANIFEST_YAML
        try:
            body = self._app.runner_config_repo_.bootstrap_runner_config(
                package_name=package_name,
                kind='manifest',
                yaml_path=seed_path,
            )
            self._manifest_file_body = body or ""
            _assert_manifest_not_empty(self._manifest_file_body, seed_path)
        except Exception as exc:
            self._app.app_trace_.record_error_and_raise('manifest.Manifest.init_manifest', exc)
