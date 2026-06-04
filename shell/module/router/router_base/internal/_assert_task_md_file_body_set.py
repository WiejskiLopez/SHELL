def _assert_task_md_file_body_set(value) -> None:
    if value is None:
        raise ValueError("task_md_file_body not loaded — call init_router_base() first")
