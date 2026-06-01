from __future__ import annotations

from shell.component.message.message_meta.message_meta import MessageMeta
from shell.component.message.message_name.internal._format_name import _format_name
from shell.component.message.message_name.internal._rename_message import _rename_message
from shell.component.message.message_name.internal._validate_name import _validate_name
from shell.utils.path.path import PathType


class MessageName:

    @staticmethod
    def format_name(meta: MessageMeta) -> str:
        return _format_name(meta)

    @staticmethod
    def is_valid_name(name: str, meta: MessageMeta) -> bool:
        return _validate_name(name, meta)

    @staticmethod
    def rename_message(path: PathType, meta: MessageMeta) -> PathType:
        return _rename_message(path, meta)
