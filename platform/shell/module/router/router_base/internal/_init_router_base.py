from __future__ import annotations

from shell.module.router.router_base.internal._assert_task_yaml_file_body_set import _assert_task_yaml_file_body_set


def _init_router_base(router_base, reader=None) -> None:
    app = router_base._app
    record = app.task_record_
    task_yaml_file_body = record.body_yaml_raw_
    _assert_task_yaml_file_body_set(task_yaml_file_body)
    app.app_node_.node_.node_task_._task_yaml_file_body = task_yaml_file_body
    app.app_node_.node_.node_task_._task_md_file_body = record.body_md_
    app.app_node_.node_.node_task_._task_name = record.name_
    router_base.graph_.init_graph()
