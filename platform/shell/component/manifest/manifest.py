"""manifest.py
Manifest: structured representation of a loaded manifest.yaml file.

Fields:
    _app          — parent App (DOM back-reference)
    _manifest_path             — path to the manifest.yaml file on disk
    _manifest_file_body — raw YAML text content of that file (str)
"""

from __future__ import annotations

from shell.utils.path.path import Path, PathType

from shell.component.manifest.internal._manifest_name import get_manifest_name
from shell.component.manifest.internal._manifest_version import get_manifest_version
from shell.component.manifest.internal._manifest_description import get_manifest_description
from shell.component.manifest.internal._assert_manifest_body_loaded import _assert_manifest_body_loaded
from shell.component.manifest.internal._assert_manifest_path_set import _assert_manifest_path_set
from shell.component.manifest.internal._assert_manifest_not_empty import _assert_manifest_not_empty
from shell.constants.constants import MANIFEST_YAML


class Manifest:
    """Raw manifest data for a single node run.

    Constructed as Manifest(app) — held as app.manifest_, the canonical
    source of manifest data for the entire run.
    """

    __slots__ = ("_app", "_manifest_path", "_manifest_file_body")

    def __init__(
        self,
        app=None,
        manifest_path: PathType | str | None = None,
        manifest_file_body: str | None = None,
    ) -> None:
        self._app = app
        self._manifest_path: PathType | None = Path.new(manifest_path) if manifest_path else None
        self._manifest_file_body: str = manifest_file_body or ""

    # ------------------------------------------------------------------ #
    # Validated properties                                                 #
    # ------------------------------------------------------------------ #

    @property
    def manifest_file_body_(self) -> str:
        """Return manifest YAML text. Raises if empty (init_manifest not called)."""
        _assert_manifest_body_loaded(self._manifest_file_body)
        return self._manifest_file_body

    @property
    def manifest_path_(self) -> PathType:
        """Return the resolved manifest path. Raises if not set."""
        _assert_manifest_path_set(self._manifest_path)
        return Path.new(self._manifest_path).resolve()

    # ------------------------------------------------------------------ #
    # Properties                                                           #
    # ------------------------------------------------------------------ #

    @property
    def _manifest_name_(self) -> str:
        return get_manifest_name(self._app)

    @property
    def manifest_version_(self) -> str:
        return get_manifest_version(self._app)

    @property
    def _manifest_description_(self) -> str:
        return get_manifest_description(self._app)

    # ------------------------------------------------------------------ #
    # DOM operation                                                        #
    # ------------------------------------------------------------------ #

    def init_manifest(self, reader=None) -> None:
        """Read manifest.yaml from the runner root and store raw text on self.

        reader: optional callable (path: PathType) -> str for testability.
        """
        if reader is None:
            reader = lambda p: p.read_text(encoding='utf-8')  # noqa: E731
        manifest_path = self._app.cli_.cli_properties_.runner_root_dir_ / MANIFEST_YAML
        try:
            self._manifest_path = manifest_path
            self._manifest_file_body = reader(manifest_path) or ""
            _assert_manifest_not_empty(self._manifest_file_body, manifest_path)
        except Exception as exc:
            self._app.app_trace_.record_error_and_raise('manifest.Manifest.init_manifest', exc)
