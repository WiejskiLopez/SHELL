from shell.utils.path.path import PathType


def _assert_task_dir_set(task_dir: PathType | None) -> None:
    if task_dir is None:
        raise RuntimeError("[NodeTask] task_dir is not set — pass --task-dir to the CLI")
