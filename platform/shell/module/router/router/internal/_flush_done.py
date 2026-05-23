from __future__ import annotations

from shell.module.router.router.parse_message_filename import SEPARATOR
from shell.module.router.router.parse_message_filename import parse_message_filename
from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_OUTPUT


def _flush_done(app, node_stage) -> None:
    app.app_trace_.record_info('router._flush_done', 'no agent output and active/ empty — flushing')
    last_message = node_stage.get_last_message()
    if last_message is not None:
        node_dir = app.app_node_.node_.node_dir_
        own_output_dir = node_dir / DOT_NODE / DIR_OUTPUT
        Path.mkdir(own_output_dir)
        parsed = parse_message_filename(last_message.name)
        if parsed is not None and parsed.msg_type == 'DONE':
            output_name = SEPARATOR.join([
                parsed.sequence_id,
                parsed.from_role,
                'analizer',
                'TASK',
                parsed.intent,
                parsed.thread_id,
                app.cli_.cli_properties_.message_id_,
                parsed.step,
            ]) + parsed.suffix
        else:
            output_name = last_message.name
        destination = own_output_dir / output_name
        Path.copy_to(last_message, destination)
        app.app_trace_.record_info('router._flush_done', f'copied {last_message.name} to {destination}')
    else:
        app.app_trace_.record_info('router._flush_done', 'no last message in history')
    app.app_trace_.record_info('router._flush_done', 'flush: done', returncode=11)
