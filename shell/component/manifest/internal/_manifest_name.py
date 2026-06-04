import yaml


def get_manifest_name(app) -> str:
    """Return the 'name' field from app.manifest_ YAML text."""
    data: dict = yaml.safe_load(app.manifest_.manifest_file_body) or {}
    value = data.get("name", "")
    if not value:
        raise ValueError("[get_manifest_name] Required manifest field missing: 'name'")
    return value
