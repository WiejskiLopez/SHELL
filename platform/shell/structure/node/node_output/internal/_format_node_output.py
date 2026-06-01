from __future__ import annotations

from shell.component.message.message.message import Message
from shell.component.message.message_envelope.message_envelope import MessageEnvelope
from shell.component.message.message_meta.message_meta import MessageMeta
from shell.component.message.message_name.message_name import MessageName
from shell.component.message.message_reader.message_reader import MessageReader
from shell.component.message.message_status.message_status import MessageStatus
from shell.component.message.message_validator.message_validator import MessageValidator
from shell.component.message.message_writer.message_writer import MessageWriter
from shell.component.message.source_type.source_type import SourceType
from shell.structure.node.node_output.internal._assert_output_files_found import _assert_output_files_found
from shell.utils.path.path import Path


def _format_node_output(node_output: object) -> None:
    node = node_output._app.app_node_.node_
    output_dir = node_output.output_dir_
    input_message_list = node.node_input_.input_message_

    pending_message = input_message_list.get_message_by_status(MessageStatus.PENDING)
    input_message_meta = pending_message.message_envelope_.message_meta_
    output_message_meta = MessageMeta.reverse_message_meta(input_message_meta)

    output_files = sorted(p for p in Path.iterdir(output_dir) if Path.is_file(p))
    _assert_output_files_found(output_files, output_dir)

    for file_path in output_files:
        body = Path.read_text(file_path)
        if MessageValidator.is_valid_message(body):
            message = MessageReader.read(file_path)
        else:
            envelope = MessageEnvelope.from_meta_and_payload(output_message_meta, body)
            message = Message.from_envelope(envelope, str(file_path), SourceType.FILE)
            MessageWriter.write(file_path, message)

        meta = message.message_envelope_.message_meta_
        if not MessageName.is_valid_name(file_path.name, meta):
            file_path = MessageName.rename_message(file_path, meta)

        node_output._output_message_.append_message(message)
