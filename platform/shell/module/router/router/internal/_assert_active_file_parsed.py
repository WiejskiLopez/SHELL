from shell.utils.path.path import PathType

from shell.module.router.router.parse_message_filename import MessageFilename


def _assert_active_file_parsed(parsed: MessageFilename | None, active_file: PathType) -> None:
    if parsed is None:
        raise ValueError(f"[Router] active file has unparseable filename: '{active_file.name}'")
    if not parsed.from_role:
        raise ValueError(f"[Router] active file has no from_role in filename: '{active_file.name}'")
