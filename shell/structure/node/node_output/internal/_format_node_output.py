from __future__ import annotations

import yaml

from shell.component.message.message.message import Message
from shell.component.message.message_envelope.message_envelope import MessageEnvelope
from shell.component.message.message_meta.message_meta import MessageMeta
from shell.component.message.message_status.message_status import MessageStatus
from shell.component.message.message_validator.message_validator import MessageValidator
from shell.component.message.source_type.source_type import SourceType
from shell.structure.node.node_output.internal._assert_output_files_found import _assert_output_files_found


def _format_node_output(node_output: object) -> None:
    node = node_output._app.app_node_.node_
    output_dir = node_output.output_dir_
    port = node.port_
    input_message_list = node.node_input_.input_message_

    pending_message = input_message_list.get_message_by_status(MessageStatus.PENDING)
    input_message_meta = pending_message.message_envelope_.message_meta_
    output_message_meta = MessageMeta.reverse_message_meta(input_message_meta)

    output_files = sorted(port.list_files(output_dir))
    _assert_output_files_found(output_files, output_dir)

    for file_path in output_files:
        body = port.read_text(file_path)
        if MessageValidator.is_valid_message(body):
            data = yaml.safe_load(body)
            envelope = MessageEnvelope()
            envelope.init_envelope_data(data)
            message = Message()
            message._message_envelope = envelope
            message._source_name = str(file_path)
            message._source_type = SourceType.FILE
        else:
            envelope = MessageEnvelope.from_meta_and_payload(output_message_meta, body)
            message = Message.from_envelope(envelope, str(file_path), SourceType.FILE)
            port.write_text(file_path, yaml.dump(envelope.to_dict(), allow_unicode=True, default_flow_style=False))

        meta = message.message_envelope_.message_meta_
        canonical_name = _format_canonical_name(meta)
        if file_path.name != canonical_name:
            new_path = file_path.parent / canonical_name
            port.move(file_path, new_path)
            file_path = new_path

        node_output._output_message_.append_message(message)


def _format_canonical_name(meta) -> str:
    parts = [
        str(meta.session_id_),
        str(meta.task_id_),
        str(meta.message_id_),
        str(meta.sender_node_),
        str(meta.target_node_),
        str(meta.message_type_.value),
        str(meta.status_.value),
        str(meta.sequence_id_),
    ]
    return "_".join(parts) + ".json"
