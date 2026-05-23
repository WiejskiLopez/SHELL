from __future__ import annotations


from shell.module.agent.agent_prompt.internal._assert_task_dir_resolved import _assert_task_dir_resolved
from shell.module.agent.agent_prompt.internal._assert_role_resolved import _assert_role_resolved
from shell.utils.path.path import Path, PathType
from shell.constants.constants import DOT_NODE, DIR_PROMPT


def _init_agent_prompt(agent_prompt) -> None:
    app = agent_prompt._app
    task_dir = app.cli_.cli_properties_.task_dir_
    source_dir = app.cli_.cli_properties_.source_dir_
    app.app_trace_.record_info('agent_prompt._init_agent_prompt._init_agent_prompt', f'task_dir={task_dir}, source_dir={source_dir}')
    role = app.app_properties_.role_
    _assert_task_dir_resolved(task_dir)
    _assert_role_resolved(role)
    prompt_dir = app.app_node_.node_.node_dir_ / DOT_NODE / DIR_PROMPT

    cli_prompt = app.cli_.cli_properties_.prompt_
    app.app_trace_.record_info('agent_prompt._init_agent_prompt._init_agent_prompt', f'cli_prompt set={cli_prompt is not None}')
    if cli_prompt is not None:
        agent_prompt.prompt_cli_.init_prompt_cli(app)
        app.app_trace_.record_info('agent_prompt._init_agent_prompt._init_agent_prompt', 'using cli prompt — skipping role/system prompt loading')
        return

    prompt_source = source_dir if source_dir is not None else task_dir
    prompt_source_files = [p.name for p in Path.iterdir(Path.new(prompt_source)) if Path.is_file(p)]
    app.app_trace_.record_info(
        'agent_prompt._init_agent_prompt._init_agent_prompt',
        f'prompt_source files: {prompt_source_files}'
    )

    app.app_trace_.record_info(
        'agent_prompt._init_agent_prompt._init_agent_prompt',
        f'loading role prompts from {prompt_source} pattern *.prompt.md (excluding *.system.*)'
    )
    task_name = app.cli_.cli_properties_.task_name_
    agent_prompt.prompt_role_.init_prompt_role(prompt_source, role, task_name, prompt_dir)
    app.app_trace_.record_info(
        'agent_prompt._init_agent_prompt._init_agent_prompt',
        f'role prompts loaded: {[p.file_name_ for p in agent_prompt.prompt_role_.file_prompts_]}'
    )

    app.app_trace_.record_info(
        'agent_prompt._init_agent_prompt._init_agent_prompt',
        f'loading system prompts from {prompt_source} pattern *.system.prompt.md (role={role}, task_name={task_name})'
    )
    agent_prompt.prompt_skill_.init_prompt_skill(prompt_source, task_name, prompt_dir)
    app.app_trace_.record_info(
        'agent_prompt._init_agent_prompt._init_agent_prompt',
        f'skill prompts loaded: {[p.file_name_ for p in agent_prompt.prompt_skill_.file_prompts_]}'
    )

    agent_prompt.prompt_system_.init_prompt_system(prompt_source, role, task_name, prompt_dir)
    app.app_trace_.record_info(
        'agent_prompt._init_agent_prompt._init_agent_prompt',
        f'system prompts loaded: {[p.file_name_ for p in agent_prompt.prompt_system_.file_prompts_]}'
    )
