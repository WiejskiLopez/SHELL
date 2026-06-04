
from shell.component.manifest.manifest import Manifest
from shell.utils.path.path import Path, PathType
from shell.constants.constants import MANIFEST_YAML


def _load_manifest(app, reader=None) -> None:
    if reader is None:
        reader = Path.read_text
    manifest_path = app.cli_.cli_properties_.runner_root_dir_ / MANIFEST_YAML
    try:
        text: str = reader(manifest_path) or ""
    except OSError as exc:
        app.app_trace_.record_error_and_raise('manifest._load_manifest._load_manifest', exc)
    app._manifest = Manifest(app, manifest_path=manifest_path, manifest_yaml=text)
