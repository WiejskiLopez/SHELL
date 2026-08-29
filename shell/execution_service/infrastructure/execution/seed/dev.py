"""Development seed data for the Execution bounded context.

Idempotent: records are inserted only when missing, so the seed can be
run repeatedly against the same database without creating duplicates.

Cross-BC references (sessions, users, projects, graph definitions) use the
shared ``dev-*`` ID convention; they are opaque string IDs here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from shell.execution_service.infrastructure.execution.seed.builders import (
    build_agent_config_execution_model,
    build_agent_execution_model,
    build_agent_skill_execution_model,
    build_edge_execution_model,
    build_edge_link_execution_model,
    build_graph_execution_model,
    build_graph_execution_state_model,
    build_node_execution_model,
    build_node_execution_result_model,
    build_node_execution_state_model,
    build_node_link_execution_model,
    build_session_execution_model,
    build_session_execution_state_model,
    build_task_execution_model,
    build_task_execution_state_model,
    build_user_execution_model,
    build_user_execution_state_model,
    build_workflow_model,
)
from shell.execution_service.infrastructure.execution.task_execution.persistence.sql.models.task_execution import (
    TaskExecutionModel,
)
from shell.execution_service.infrastructure.execution.workflow.persistence.sql.models.workflow import (
    WorkflowModel,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

DEV_ID_PREFIX = "dev"
DEV_ROOT = f"devroot/{DEV_ID_PREFIX}"
DESIGN_DOC_PATH = f"{DEV_ROOT}/planner/design.md"

_GRAPH_NODE_DEFINITIONS: dict[str, list[dict[str, object]]] = {
    f"{DEV_ID_PREFIX}-graph-simple-agent": [
        {
            "id": f"{DEV_ID_PREFIX}-gnode-agent-1",
            "mode": "agent",
            "role": "agent",
            "node_type": "agent",
        },
    ],
    f"{DEV_ID_PREFIX}-graph-planner-worker": [
        {
            "id": f"{DEV_ID_PREFIX}-gnode-planner-1",
            "mode": "planner",
            "role": "planner",
            "node_type": "planner",
        },
        {
            "id": f"{DEV_ID_PREFIX}-gnode-worker-1",
            "mode": "worker",
            "role": "worker",
            "node_type": "worker",
        },
    ],
    f"{DEV_ID_PREFIX}-graph-full-pipeline": [
        {
            "id": f"{DEV_ID_PREFIX}-gnode-tasker-1",
            "mode": "tasker",
            "role": "tasker",
            "node_type": "tasker",
        },
        {
            "id": f"{DEV_ID_PREFIX}-gnode-router-1",
            "mode": "router",
            "role": "router",
            "node_type": "router",
        },
        {
            "id": f"{DEV_ID_PREFIX}-gnode-agent-2",
            "mode": "agent",
            "role": "agent",
            "node_type": "agent",
        },
    ],
}

_TASKS_DATA: list[tuple[dict[str, Any], dict[str, object], dict[str, object]]] = [
    (
        {
            "task_execution_id": f"{DEV_ID_PREFIX}-task-simple-1",
            "status": "completed",
            "name": "simple-analysis-task",
            "work_dir": f"{DEV_ROOT}/simple/analysis",
            "workflow_id": f"{DEV_ID_PREFIX}-workflow-simple",
        },
        {
            "description": "# Simple Analysis\nAnalyze the codebase.",
            "repo_url": "https://github.com/example/repo",
            "branch": "main",
        },
        {"result": "success", "issues_found": 3},
    ),
    (
        {
            "task_execution_id": f"{DEV_ID_PREFIX}-task-simple-2",
            "status": "running",
            "name": "simple-fix-task",
            "work_dir": f"{DEV_ROOT}/simple/fix",
            "workflow_id": f"{DEV_ID_PREFIX}-workflow-simple",
        },
        {"issue_ids": ["ISS-1", "ISS-2", "ISS-3"]},
        {},
    ),
    (
        {
            "task_execution_id": f"{DEV_ID_PREFIX}-task-planner-1",
            "status": "completed",
            "name": "planner-design-task",
            "work_dir": f"{DEV_ROOT}/planner/design",
            "workflow_id": f"{DEV_ID_PREFIX}-workflow-planner",
        },
        {"objective": "Design authentication module", "language": "python"},
        {"design_doc": DESIGN_DOC_PATH, "approved": True},
    ),
    (
        {
            "task_execution_id": f"{DEV_ID_PREFIX}-task-planner-2",
            "status": "created",
            "name": "planner-implement-task",
            "work_dir": f"{DEV_ROOT}/planner/implement",
            "workflow_id": f"{DEV_ID_PREFIX}-workflow-planner",
        },
        {"design_ref": DESIGN_DOC_PATH, "modules": ["auth", "session"]},
        {},
    ),
    (
        {
            "task_execution_id": f"{DEV_ID_PREFIX}-task-pipeline-1",
            "status": "completed",
            "name": "pipeline-analysis-task",
            "work_dir": f"{DEV_ROOT}/pipeline/analysis",
            "workflow_id": f"{DEV_ID_PREFIX}-workflow-pipeline",
        },
        {"project_path": f"{DEV_ROOT}/project", "pipeline_stage": "analysis"},
        {"requirements": ["req-1", "req-2"], "priority": "high"},
    ),
    (
        {
            "task_execution_id": f"{DEV_ID_PREFIX}-task-pipeline-2",
            "status": "running",
            "name": "pipeline-execute-task",
            "work_dir": f"{DEV_ROOT}/pipeline/execute",
            "workflow_id": f"{DEV_ID_PREFIX}-workflow-pipeline",
        },
        {"stage": "build", "artifacts": ["src/", "tests/"]},
        {},
    ),
]

_WORKFLOWS_DATA: list[dict[str, str]] = [
    {
        "id": f"{DEV_ID_PREFIX}-workflow-simple",
        "status": "done",
        "session_id": f"{DEV_ID_PREFIX}-session-alice-1",
        "project_id": f"{DEV_ID_PREFIX}-project-alpha",
        "graph_def_id": f"{DEV_ID_PREFIX}-graph-simple-agent",
        "user_id": f"{DEV_ID_PREFIX}-user-alice",
        "task_id_1": f"{DEV_ID_PREFIX}-task-simple-1",
        "task_id_2": f"{DEV_ID_PREFIX}-task-simple-2",
    },
    {
        "id": f"{DEV_ID_PREFIX}-workflow-planner",
        "status": "running",
        "session_id": f"{DEV_ID_PREFIX}-session-bob-1",
        "project_id": f"{DEV_ID_PREFIX}-project-beta",
        "graph_def_id": f"{DEV_ID_PREFIX}-graph-planner-worker",
        "user_id": f"{DEV_ID_PREFIX}-user-bob",
        "task_id_1": f"{DEV_ID_PREFIX}-task-planner-1",
        "task_id_2": f"{DEV_ID_PREFIX}-task-planner-2",
    },
    {
        "id": f"{DEV_ID_PREFIX}-workflow-pipeline",
        "status": "idle",
        "session_id": f"{DEV_ID_PREFIX}-session-charlie-1",
        "project_id": f"{DEV_ID_PREFIX}-project-gamma",
        "graph_def_id": f"{DEV_ID_PREFIX}-graph-full-pipeline",
        "user_id": f"{DEV_ID_PREFIX}-user-charlie",
        "task_id_1": f"{DEV_ID_PREFIX}-task-pipeline-1",
        "task_id_2": f"{DEV_ID_PREFIX}-task-pipeline-2",
    },
]


def seed_dev_sync(session: Session) -> None:
    """Insert dev task executions and workflow scenario records when missing."""
    for task_params, input_state, output_state in _TASKS_DATA:
        task_model = build_task_execution_model(**task_params)
        existing_task = session.execute(
            select(TaskExecutionModel).where(TaskExecutionModel.id == task_model.id)
        ).scalar_one_or_none()
        if existing_task is not None:
            continue

        session.add(task_model)
        session.add(
            build_task_execution_state_model(
                state_id=f"{task_model.id}-input",
                task_execution_id=task_model.id,
                direction="INPUT",
                state_data=input_state,
            )
        )
        if output_state:
            session.add(
                build_task_execution_state_model(
                    state_id=f"{task_model.id}-output",
                    task_execution_id=task_model.id,
                    direction="OUTPUT",
                    state_data=output_state,
                )
            )

    for workflow_data in _WORKFLOWS_DATA:
        existing_workflow = session.execute(
            select(WorkflowModel).where(WorkflowModel.id == workflow_data["id"])
        ).scalar_one_or_none()
        if existing_workflow is not None:
            continue

        session.add(
            build_workflow_model(
                workflow_id=workflow_data["id"],
                status=workflow_data["status"],
                session_id=workflow_data["session_id"],
                project_id=workflow_data["project_id"],
            )
        )

        _seed_execution_hierarchy(session, workflow_data)


def _seed_execution_hierarchy(session: Session, workflow_data: dict[str, str]) -> None:
    user_execution_id = f"{workflow_data['id']}-user-exec"
    session_execution_id = f"{workflow_data['id']}-session-exec"

    session.add(
        build_user_execution_model(
            user_execution_id=user_execution_id,
            user_id=workflow_data["user_id"],
        )
    )
    for direction in ("INPUT", "OUTPUT"):
        session.add(
            build_user_execution_state_model(
                state_id=f"{user_execution_id}-state-{direction.lower()}",
                user_execution_id=user_execution_id,
                direction=direction,
                state_data={"workflow_id": workflow_data["id"], "action": direction.lower()},
            )
        )

    session.add(
        build_session_execution_model(
            session_execution_id=session_execution_id,
            user_execution_id=user_execution_id,
            session_id=workflow_data["session_id"],
        )
    )
    for direction in ("INPUT", "OUTPUT"):
        session.add(
            build_session_execution_state_model(
                state_id=f"{session_execution_id}-state-{direction.lower()}",
                session_execution_id=session_execution_id,
                direction=direction,
                state_data={"workflow_id": workflow_data["id"], "step": direction.lower()},
            )
        )

    graph_definition_id = workflow_data["graph_def_id"]
    node_definitions = _GRAPH_NODE_DEFINITIONS[graph_definition_id]
    task_ids = [workflow_data["task_id_1"], workflow_data["task_id_2"]]

    for task_index, task_id in enumerate(task_ids):
        _seed_graph_execution(
            session,
            workflow_data,
            graph_definition_id,
            node_definitions,
            task_id,
            task_index,
        )


def _seed_graph_execution(
    session: Session,
    workflow_data: dict[str, str],
    graph_definition_id: str,
    node_definitions: list[dict[str, object]],
    task_id: str,
    task_index: int,
) -> None:
    graph_execution_id = f"{workflow_data['id']}-ge-{task_index}"
    tags: dict[str, object] = {
        "workflow": workflow_data["id"],
        "task": task_id,
        "env": "dev",
        "priority": "normal",
    }
    is_completed = task_index == 0

    session.add(
        build_graph_execution_model(
            graph_execution_id=graph_execution_id,
            task_execution_id=task_id,
            graph_definition_id=graph_definition_id,
            status="completed" if is_completed else "running",
            parent_graph_execution_id=None,
            state_input={"task": task_id},
            state_output={"result": "ok"} if is_completed else {},
            depth=0,
            timeout_at=None,
            correlation_id=f"corr-{workflow_data['id']}-{task_index}",
            tags=tags,
        )
    )
    session.add(
        build_graph_execution_state_model(
            state_id=f"{graph_execution_id}-state-input",
            graph_execution_id=graph_execution_id,
            direction="INPUT",
            state_data={"task_id": task_id, "mode": "auto"},
        )
    )
    session.add(
        build_graph_execution_state_model(
            state_id=f"{graph_execution_id}-state-output",
            graph_execution_id=graph_execution_id,
            direction="OUTPUT",
            state_data={"status": "completed", "message": "Done"},
        )
    )

    node_execution_ids: list[str] = []
    for position, node_definition in enumerate(node_definitions):
        node_execution_id = _seed_node_execution(
            session,
            workflow_data,
            graph_execution_id,
            node_definition,
            task_id,
            position,
            is_completed,
        )
        node_execution_ids.append(node_execution_id)

    _seed_edge_execution(session, workflow_data, graph_execution_id, node_execution_ids)


def _seed_node_execution(
    session: Session,
    workflow_data: dict[str, str],
    graph_execution_id: str,
    node_definition: dict[str, object],
    task_id: str,
    position: int,
    is_completed: bool,
) -> str:
    node_mode = str(node_definition["mode"])
    node_type = str(node_definition["node_type"])
    node_execution_id = f"{graph_execution_id}-node-{position}"

    session.add(
        build_node_execution_model(
            node_execution_id=node_execution_id,
            position=position,
            node_type=node_type,
            model="gpt-4",
            command="",
            retries=1,
            log_level="INFO",
            max_step=10,
            no_ask_user=False,
            autopilot=True,
            task_execution_id=task_id,
            source_dir=f"{DEV_ROOT}/{node_mode}",
            status="completed" if is_completed else "pending",
            status_initial="",
        )
    )
    session.add(
        build_node_link_execution_model(
            link_id=f"{graph_execution_id}-{node_execution_id}",
            graph_execution_id=graph_execution_id,
            node_execution_id=node_execution_id,
        )
    )
    for direction in ("INPUT", "OUTPUT"):
        session.add(
            build_node_execution_state_model(
                state_id=f"{node_execution_id}-state-{direction.lower()}",
                node_execution_id=node_execution_id,
                direction=direction,
                state_data={
                    "mode": node_mode,
                    "position": position,
                    "step": direction.lower(),
                },
            )
        )

    if is_completed:
        session.add(
            build_node_execution_result_model(
                result_id=f"{node_execution_id}-result",
                node_execution_id=node_execution_id,
                workflow_id=workflow_data["id"],
                status="completed",
                stdout=f"[{node_mode}] Task completed successfully.\nPosition: {position}",
                stderr="",
                artifact_uri=f"file://{DEV_ROOT}/results/{node_mode}-{position}.json",
            )
        )

    if node_type == "agent":
        _seed_agent_execution(session, node_execution_id)

    return node_execution_id


def _seed_agent_execution(session: Session, node_execution_id: str) -> None:
    agent_execution_id = f"{node_execution_id}-agent-exec"
    session.add(
        build_agent_execution_model(
            agent_execution_id=agent_execution_id,
            node_execution_id=node_execution_id,
        )
    )
    session.add(
        build_agent_config_execution_model(
            config_id=f"{agent_execution_id}-config",
            agent_execution_id=agent_execution_id,
            config_data='{"model": "gpt-4", "temperature": 0.7, "max_tokens": 2048, "top_p": 0.9}',
        )
    )
    for skill_index in (1, 2):
        session.add(
            build_agent_skill_execution_model(
                skill_id=f"{agent_execution_id}-skill-{skill_index}",
                agent_execution_id=agent_execution_id,
                skill_data={
                    "name": f"agent-skill-{skill_index}",
                    "category": "coding" if skill_index == 1 else "analysis",
                },
            )
        )


def _seed_edge_execution(
    session: Session,
    workflow_data: dict[str, str],
    graph_execution_id: str,
    node_execution_ids: list[str],
) -> None:
    edge_execution_id = f"{graph_execution_id}-edge-0"
    source_node_id = node_execution_ids[0]
    target_node_id = node_execution_ids[1] if len(node_execution_ids) > 1 else None

    session.add(
        build_edge_execution_model(
            edge_execution_id=edge_execution_id,
            edge_definition_id=f"{workflow_data['graph_def_id']}-edge-def-0",
            source_node_execution_id=source_node_id,
            target_node_execution_id=target_node_id,
        )
    )
    session.add(
        build_edge_link_execution_model(
            link_id=f"{edge_execution_id}-link-0",
            node_execution_id=source_node_id,
            edge_execution_id=edge_execution_id,
        )
    )


__all__ = ["DEV_ID_PREFIX", "seed_dev_sync"]
