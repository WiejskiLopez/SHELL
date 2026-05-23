from __future__ import annotations

from shell.component.message.message.message import Message
from shell.component.message.message_reader.internal._read_message_file import _read_message_file
from shell.utils.path.path import Path, PathType


class MessageReader:
    """
    Slots:
        _path — path to the message file
    """

    __slots__ = ("_path",)

    def __init__(self) -> None:
        self._path: PathType | None = None

    @property
    def path_(self) -> PathType:
        return self._path

    def read_message_file(self) -> Message:
        return _read_message_file(self)

    @staticmethod
    def read(path: PathType) -> Message:
        reader = MessageReader()
        reader._path = path
        return reader.read_message_file()
