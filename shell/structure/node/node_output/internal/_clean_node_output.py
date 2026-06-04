from __future__ import annotations


def _clean_node_output(node_output) -> None:
    port = node_output._app.app_node_.node_.port_
    output_dir = node_output.output_dir_
    if not port.exists(output_dir):
        return
    for item in port.list_files(output_dir):
        try:
            port.unlink(item)
        except OSError:
            pass
