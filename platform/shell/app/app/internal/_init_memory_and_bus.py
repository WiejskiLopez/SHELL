"""_init_memory_and_bus.py
Initialize Memory + MessageBus + WorkflowState for the App.

DB lives at <runner_root_dir>/.shell/shell.db (single DB per runner).
Memory is the foundation; bus and workflow_state share its driver.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.memory.memory.memory import Memory
from shell.memory.sql_memory_backend.sql_memory_backend import SqlMemoryBackend
from shell.memory.sql_driver.sqlite_driver.sqlite_driver import SqliteDriver
from shell.memory.rag_index.embedder.hash_embedder import HashEmbedder
from shell.utils.path.path import Path

if TYPE_CHECKING:
    from shell.app.app.app import App


def _init_memory_and_bus(app: 'App') -> None:
    runner_root = app.cli_.cli_properties_.runner_root_dir_
    shell_dir = runner_root / ".shell"
    if not Path.exists(shell_dir):
        Path.mkdir(shell_dir)
    db_path = shell_dir / "shell.db"

    driver = SqliteDriver(db_path)
    backend = SqlMemoryBackend(driver)
    app.memory_.init_memory(backend, HashEmbedder())

    app.bus_.init_message_bus(app.memory_.driver_)
    app.workflow_state_.init_workflow_state(app.memory_.driver_)
    app.task_repo_.init_task_repo(app.memory_.driver_)
    app.prompt_repo_.init_prompt_repo(app.memory_.driver_)
    app.node_result_repo_.init_node_result_repo(app.memory_.driver_)
    app.runner_config_repo_.init_runner_config_repo(app.memory_.driver_)

    task_id = app.cli_.cli_properties_.task_id_
    if task_id is not None:
        record = app.task_repo_.get_task_by_id(task_id)
        if record is None:
            raise RuntimeError(f"--task-id {task_id} not found in task DB at {db_path}")
        app.set_task_record(record)
        app.app_trace_.record_info(
            'app._init_memory_and_bus',
            f'loaded task_record from DB by --task-id={task_id} (name={record.name_} ver={record.version_})',
        )
