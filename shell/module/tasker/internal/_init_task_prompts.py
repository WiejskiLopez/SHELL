from __future__ import annotations


from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE, DIR_TASK


def _init_task_prompts(app) -> None:
    task_dir = Path.resolve(app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK)
    source_dir = Path.new(app.cli_.cli_properties_.source_dir_)

    for source_prompt in Path.glob(source_dir, '*.prompt.md'):
        dest = task_dir / source_prompt.name
        if not Path.is_file(dest):
            Path.copy_to(source_prompt, dest)
            app.app_trace_.record_info(
                'tasker._init_task_prompts._init_task_prompts',
                f'copy {source_prompt} -> {dest}'
            )
