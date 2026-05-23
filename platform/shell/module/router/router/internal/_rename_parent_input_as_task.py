from shell.utils.path.path import PathType
from __future__ import annotations


from shell.module.router.router.parse_message_filename import SEPARATOR
from shell.module.router.router.parse_message_filename import parse_message_filename


def _rename_parent_input_as_task(parent_file: PathType, app, first_role: str, own_role: str) -> PathType:
    message_id = app.cli_.cli_properties_.message_id_
    thread_id = app.cli_.cli_properties_.thread_id_
    parsed = parse_message_filename(parent_file.name)
    intent = parsed.intent if parsed is not None else parent_file.stem
    suffix = parent_file.suffix
    new_name = SEPARATOR.join([
        '1', own_role, first_role, 'TASK', intent, thread_id, message_id, '1'
    ]) + suffix
    new_path = parent_file.parent / new_name
    parent_file.rename(new_path)
    return new_path
