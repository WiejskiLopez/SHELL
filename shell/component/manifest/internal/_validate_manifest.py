import yaml


def _validate_manifest(app) -> None:
    """Raise if any of the required manifest fields are missing from app.manifest_.

    Required: name, version, description.
    """
    data: dict = yaml.safe_load(app.manifest_.manifest_file_body) or {}
    for field in ('name', 'version', 'description'):
        if not data.get(field):
            raise ValueError(f"[_validate_manifest] Required manifest field missing: '{field}'")
