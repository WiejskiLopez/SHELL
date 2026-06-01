from __future__ import annotations

from shell.component.message.message.message import Message
from shell.component.message.message_writer.internal._write_message_file import _write_message_file
from shell.utils.path.path import Path, PathType


class MessageWriter:
    """
    Slots:
        _path    — path to the output file
        _message — message to write
    """

    __slots__ = ("_path", "_message")

    def __init__(self) -> None:
        self._path: PathType | None = None
        self._message: Message | None = None

    @property
    def path_(self) -> PathType:
        return self._path

    @property
    def message_(self) -> Message:
        return self._message

    def write_message_file(self) -> None:
        _write_message_file(self)

    @staticmethod
    def write(path: PathType, message: Message) -> None:
        writer = MessageWriter()
        writer._path = path
        writer._message = message
        writer.write_message_file()
