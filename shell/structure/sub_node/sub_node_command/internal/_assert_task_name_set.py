def _assert_task_name_set(task_name) -> None:
    if not task_name:
        raise RuntimeError("[SubNodeCommand] task_name is not set — pass --task-name to the CLI")
