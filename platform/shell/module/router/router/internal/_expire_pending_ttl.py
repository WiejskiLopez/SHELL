from __future__ import annotations

from shell.module.router.router.parse_message_filename import parse_message_filename


def _expire_pending_ttl(app, node_stage, max_step: int) -> None:
    for pending_file in node_stage.get_pending_files():
        pending_parsed = parse_message_filename(pending_file.name)
        if pending_parsed is not None:
            try:
                if int(pending_parsed.step) > max_step:
                    app.app_trace_.record_info(
                        'router._expire_pending_ttl',
                        f'pending expired ttl: {pending_file.name}'
                    )
                    node_stage.move_to_ignored(pending_file.name)
            except ValueError:
                pass
