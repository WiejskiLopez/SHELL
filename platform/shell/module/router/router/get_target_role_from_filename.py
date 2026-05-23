from shell.utils.path.path import Path, PathType


def get_target_role_from_filename(filename: str, roles: set) -> str | None:
    """Return role if the stem ends with _<role>, else None."""
    stem = Path.new(filename).stem
    parts = stem.rsplit('_', 1)
    if len(parts) == 2 and parts[-1] in roles:
        return parts[-1]
    return None
