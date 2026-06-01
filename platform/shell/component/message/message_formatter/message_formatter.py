from __future__ import annotations

from shell.component.message.message.message import Message
from shell.component.message.message_formatter.internal._format_message_file import _format_message_file
from shell.component.message.message_meta.message_meta import MessageMeta
from shell.utils.path.path import PathType


class MessageFormatter:
    """
    Slots:
        _path — path to the file to format
    """

    __slots__ = ("_path",)

    def __init__(self) -> None:
        self._path: PathType | None = None

    @property
    def path_(self) -> PathType:
        return self._path

    def format_message_file(self, message_meta: MessageMeta | None = None) -> Message:
        return _format_message_file(self, message_meta)
