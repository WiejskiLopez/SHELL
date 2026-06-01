from __future__ import annotations

from shell.component.message.message_meta.message_meta import MessageMeta
from shell.component.message.message_name.internal._format_name import _format_name
from shell.utils.path.path import Path, PathType


def _rename_message(path: PathType, meta: MessageMeta) -> PathType:
    new_name = _format_name(meta)
    new_path = Path.new(path.parent, new_name)
    Path.move(path, new_path)
    return new_path
