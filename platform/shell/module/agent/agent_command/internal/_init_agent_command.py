from __future__ import annotations

import os
import shutil

from shell.module.agent.agent_command.internal._assert_copilot_cmd_found import _assert_copilot_cmd_found
from shell.module.agent.agent_command.internal._assert_model_set import _assert_model_set
from shell.module.agent.agent_command.internal._assert_output_dir_exists import _assert_output_dir_exists
from shell.module.agent.agent_command.internal._assert_log_dir_exists import _assert_log_dir_exists
from shell.module.agent.agent_command.internal._assert_add_dir_exists import _assert_add_dir_exists
from shell.constants.constants import DOT_NODE, DIR_OUTPUT


def _init_agent_command(agent_command) -> None:
    which = agent_command._which or shutil.which
    os_name = agent_command._os_name or os.name
    app = agent_command._app

    binary = which("copilot")
    _assert_copilot_cmd_found(binary)

    if os_name == "nt" and str(binary).lower().endswith((".cmd", ".bat")):
        agent_command.command_.extend_command_args(["cmd", "/c", binary])
    else:
        agent_command.command_.add_command_arg(binary)

    model = (app.runner_.agent_.agent_properties_.model_ or "").strip()
    _assert_model_set(model)
    agent_command.command_.extend_command_args(["--model", model])

    if app.cli_.cli_properties_.is_allow_all_paths_:
        agent_command.command_.add_command_arg("--allow-all-paths")

    if app.cli_.cli_properties_.is_allow_all_tools_:
        agent_command.command_.add_command_arg("--allow-all-tools")

    agent_command.command_.extend_command_args(["--output-format", app.cli_.cli_properties_.output_format_])


    if app.cli_.cli_properties_.is_no_ask_user_:
        agent_command.command_.add_command_arg("--no-ask-user")

    if app.cli_.cli_properties_.is_autopilot_:
        agent_command.command_.add_command_arg("--autopilot")

    output_dir = app.app_node_.node_.node_dir_ / DOT_NODE / DIR_OUTPUT
    _assert_output_dir_exists(output_dir)
    agent_command.command_.extend_command_args(["--add-dir", str(output_dir)])
    app.app_trace_.record_info('agent_command._init_agent_command', f'--add-dir {output_dir}')

    logs_dir = app.app_node_.node_.node_logs_.logs_dir_
    _assert_log_dir_exists(logs_dir)

    for add_dir in app.cli_.cli_properties_.add_dirs_:
        _assert_add_dir_exists(add_dir)
        agent_command.command_.extend_command_args(["--add-dir", str(add_dir)])
        app.app_trace_.record_info('agent_command._init_agent_command', f'--add-dir {add_dir}')

    node_dir = app.app_node_.node_.node_dir_
    _assert_add_dir_exists(node_dir)
    agent_command.command_.extend_command_args(["--add-dir", str(node_dir)])
    app.app_trace_.record_info('agent_command._init_agent_command', f'--add-dir {node_dir}')

    agent_command.command_.extend_command_args(["--log-dir", str(logs_dir)])
    app.app_trace_.record_info('agent_command._init_agent_command', f'--log-dir {logs_dir}')

