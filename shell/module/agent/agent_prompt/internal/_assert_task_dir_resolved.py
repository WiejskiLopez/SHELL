def _assert_task_dir_resolved(task_dir) -> None:
    if task_dir is None:
        raise ValueError("task_dir is not set — required for prompt_role loading")
