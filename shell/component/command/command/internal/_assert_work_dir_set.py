def _assert_work_dir_set(work_dir) -> None:
    if not work_dir:
        raise RuntimeError("[Command] work_dir is not set — pass --work-dir to the CLI")
