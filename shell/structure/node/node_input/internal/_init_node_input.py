from __future__ import annotations

import yaml

from shell.component.message.message.message import Message
from shell.component.message.message_envelope.message_envelope import MessageEnvelope
from shell.component.message.message_list.message_list import MessageList
from shell.component.message.source_type.source_type import SourceType
from shell.constants.constants import DOT_NODE, DIR_INPUT


def _init_node_input(node_input) -> None:
    node = node_input._app.app_node_.node_
    node_input._input_dir = Path.resolve(node.node_dir_ / DOT_NODE / DIR_INPUT)
    port = node.port_

    messages = []
    for path in port.list_files(node_input._input_dir, ".yaml") + port.list_files(node_input._input_dir, ".yml"):
        raw = port.read_text(path)
        data = yaml.safe_load(raw)
        envelope = MessageEnvelope()
        envelope.init_envelope_data(data)
        message = Message()
        message._message_envelope = envelope
        message._source_name = str(path)
        message._source_type = SourceType.FILE
        messages.append(message)

    message_list = MessageList()
    message_list._messages = messages
    node_input._input_message = message_list
