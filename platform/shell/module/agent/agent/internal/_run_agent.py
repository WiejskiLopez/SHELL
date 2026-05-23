"""run_agent.py
Responsible for one thing: running the CLI command via subprocess,
capturing stdout/stderr, handling TimeoutExpired and retries.
Writes stdout, stderr, returncode to app.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from subprocess import CompletedProcess

from shell.module.agent.agent.internal._run_once import _run_once
from shell.module.agent.agent.internal._assert_prompt_not_empty import _assert_prompt_not_empty
from shell.status.status import Status


def _run_agent(
    agent,
    runner: Callable[..., CompletedProcess] | None = None,
    sleep: Callable[[float], None] | None = None,
) -> Status:
    """Run the CLI command with optional retries.

    Prompt is passed via stdin.
    Writes stdout, stderr, returncode to app.
    After all attempts failed: escalates to error and raises.
    runner: optional callable replacing subprocess.run (for testing).
    sleep: optional callable replacing time.sleep (for testing).
    """
    if sleep is None:
        sleep = time.sleep
    app = agent._app
    cmd: list[str] = agent._agent_command.command_
    timeout: int = app.runner_.agent_.agent_properties_.timeout_
    retries: int = app.runner_.agent_.agent_properties_.retries_
    retry_delay: float = app.runner_.agent_.agent_properties_.retry_delay_
    prompt: str = app.runner_.agent_.agent_prompt_.prompt()
    cli = app.cli_
    app.app_trace_.record_info('agent._run_agent._run_agent', f'parent_thread_id={cli.parent_thread_id_} thread_id={cli.thread_id_}')
    binds = [(name, value) for name, value in app.placeholders_.placeholder_list_]
    app.app_trace_.record_info('agent._run_agent._run_agent', f'placeholders before apply: {binds}')
    prompt = app.placeholders_.apply(prompt)
    _assert_prompt_not_empty(prompt)
    app.app_trace_.record_info('agent._run_agent._run_agent', f'cmd: {cmd}')
    app.app_trace_.record_info('agent._run_agent._run_agent', f'cwd: {app.app_node_.node_.node_dir_}')
    app.app_trace_.record_info('agent._run_agent._run_agent', f'timeout={timeout} retries={retries} retry_delay={retry_delay}')
    app.app_trace_.record_info('agent._run_agent._run_agent', f'prompt ({len(prompt)} chars):\n{prompt}')

    for attempt in range(retries + 1):

        status = _run_once(cmd=cmd, prompt=prompt, timeout=timeout, app=app, runner=runner)

        if status == Status.SUCCESS:
            app.app_trace_.record_info('agent._run_agent._run_agent', f'Command succeeded on attempt {attempt + 1}.')
            return status

        if attempt < retries:
            app.app_trace_.record_info('agent._run_agent._run_agent', f"Retry {attempt + 1}/{retries} after {retry_delay:.1f}s...")
            sleep(retry_delay)

    app.app_trace_.record_error_and_raise('agent._run_agent._run_agent', RuntimeError(f'Command failed after {retries + 1} attempt(s).'))
