from __future__ import annotations


from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE, DIR_INPUT


def _seed_tasker_input_to_first_agent(app, agent_nodes) -> bool:
    task_dir = app.cli_.cli_properties_.task_dir_
    if task_dir is None:
        return False
    tasker_input_dir = task_dir.parent / DIR_INPUT
    if not Path.exists(tasker_input_dir):
        return False
    files = [f for f in Path.iterdir(tasker_input_dir) if Path.is_file(f)]
    if not files:
        return False
    if not agent_nodes:
        return False
    first_agent_input = agent_nodes[0].sub_node_properties_.node_dir_ / DOT_NODE / DIR_INPUT
    Path.mkdir(first_agent_input)
    for f in files:
        dest = first_agent_input / f.name
        Path.move(f, dest)
        app.app_trace_.record_info(
            'router._seed_tasker_input_to_first_agent',
            f'moved {f.name} from tasker input to {agent_nodes[0].node_name_} input'
        )
    return True
