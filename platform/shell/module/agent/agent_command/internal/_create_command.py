"""create_command.py
Responsible for one thing: assembling the Copilot CLI command as a list
of arguments ready for subprocess.run.

Requires either app.command or a 'copilot' binary in PATH.
"""

import os
import shutil

from shell.module.agent.agent_command.internal._assert_copilot_cmd_found import _assert_copilot_cmd_found
from shell.module.agent.agent_command.internal._assert_model_set import _assert_model_set
from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_OUTPUT, DIR_LOGS


def _create_command(app, which=None, os_name=None) -> list[str]:
    """Build and return the Copilot CLI command argument list.

    Raises FileNotFoundError when the Copilot binary cannot be located.
    which:   optional callable (name: str) -> str | None (defaults to shutil.which).
    os_name: optional str to override os.name for testability.
    """
    if which is None:
        which = shutil.which
    if os_name is None:
        os_name = os.name

    command = which("copilot")
    _assert_copilot_cmd_found(command)

    cmd: list[str] = [command]

    if os_name == "nt" and str(command).lower().endswith((".cmd", ".bat")):
        cmd = ["cmd", "/c"] + cmd
    model = (app.runner_.agent_.agent_properties_.model_ or "").strip()
    _assert_model_set(model)
    cmd.extend(["--model", model])

    cmd.extend(["--allow-all-paths", "--allow-all-tools", "--output-format", "json"])

    if app.cli_.cli_properties_.is_no_ask_user_:
        cmd.append("--no-ask-user")

    if app.cli_.cli_properties_.is_autopilot_:
        cmd.append("--autopilot")

    add_dirs: list[str] = []

    for directory in app.cli_.cli_properties_.add_dirs_:
        d = str(directory).strip()
        if d:
            add_dirs.append(d)

    output_dir = app.app_node_.node_.node_dir_ / DOT_NODE / DIR_OUTPUT
    Path.mkdir(output_dir)
    add_dirs.append(output_dir.as_posix())
    add_dirs.append(app.app_node_.node_.node_dir_.as_posix())

    log_dir = app.app_node_.node_.node_dir_ / DOT_NODE / DIR_LOGS
    Path.mkdir(log_dir)

    for add_dir in add_dirs:
        cmd.extend(["--add-dir", add_dir])
        app.app_trace_.record_info('agent_command._create_command', f'--add-dir {add_dir}')

    cmd.extend(["--log-dir", log_dir.as_posix()])
    app.app_trace_.record_info('agent_command._create_command', f'--log-dir {log_dir.as_posix()}')

    return cmd
