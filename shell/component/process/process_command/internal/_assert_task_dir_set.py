def _assert_task_dir_set(task_dir) -> None:
    if not task_dir:
        raise RuntimeError("[ProcessCommand] task_dir is not set — pass --task-dir to the CLI")
