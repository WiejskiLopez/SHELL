from __future__ import annotations

from shell.component.message.message_list.message_list import MessageList
from shell.component.message.message_reader.message_reader import MessageReader
from shell.structure.node.node_input.internal._assert_input_dir_exists import _assert_input_dir_exists
from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_INPUT

_MESSAGE_SUFFIXES = {".yaml", ".yml"}


def _init_node_input(node_input) -> None:
    node_input._input_dir = (node_input._app.app_node_.node_.node_dir_ / DOT_NODE / DIR_INPUT).resolve()
    _assert_input_dir_exists(node_input._input_dir)

    messages = []
    for path in sorted(p for p in Path.iterdir(node_input.input_dir_) if Path.is_file(p) and p.suffix.lower() in _MESSAGE_SUFFIXES):
        reader = MessageReader()
        reader._path = path
        messages.append(reader.read_message_file())

    message_list = MessageList()
    message_list._messages = messages
    node_input._input_message = message_list
