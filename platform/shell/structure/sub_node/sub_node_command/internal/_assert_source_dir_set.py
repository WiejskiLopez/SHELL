from shell.utils.path.path import PathType


def _assert_source_dir_set(source_dir) -> None:
    if not source_dir:
        raise RuntimeError("[SubNodeCommand] source_dir is not set — pass --source-dir to the CLI")
