import yaml


def get_manifest_version(app) -> str:
    """Return the 'version' field from app.manifest_ YAML text."""
    data: dict = yaml.safe_load(app.manifest_.manifest_file_body_) or {}
    value = data.get("version", "")
    if not value:
        raise ValueError("[get_manifest_version] Required manifest field missing: 'version'")
    return value
