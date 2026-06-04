import yaml


def get_manifest_description(app) -> str:
    """Return the 'description' field from app.manifest_ YAML text."""
    data: dict = yaml.safe_load(app.manifest_.manifest_file_body) or {}
    value = data.get("description", "")
    if not value:
        raise ValueError("[get_manifest_description] Required manifest field missing: 'description'")
    return value
