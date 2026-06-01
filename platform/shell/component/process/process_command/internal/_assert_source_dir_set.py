def _assert_source_dir_set(source_dir) -> None:
    if not source_dir:
        raise RuntimeError("[ProcessCommand] source_dir is not set — pass --source-dir to the CLI")
