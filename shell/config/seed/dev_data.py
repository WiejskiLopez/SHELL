"""Dev seed data — comprehensive test data for local development.

Creates 3-10 realistic, coherent sample records in every table
across all bounded contexts.  Only invoked when seed_dev_data is
enabled (dev profile or SHELL_SEED_DEV_DATA=true).

Usage:
    python -m shell.config.seed --url sqlite+aiosqlite:///shell_dev.db
"""

from __future__ import annotations

import argparse
import os
import tempfile
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from sqlalchemy.engine import Connection

_DEV_ID_PREFIX = "dev"
_DEV_ROOT = f"{tempfile.gettempdir()}/shell/dev"

_NOW = datetime.now(tz=UTC)


async def seed_dev_data(url: str) -> None:
    """Seed comprehensive development data into the database."""
    engine = create_async_engine(url, echo=False, future=True)

    async with engine.begin() as conn:
        await conn.run_sync(_seed_dev_sync)

    await engine.dispose()


def _seed_dev_sync(sync_conn: Connection) -> None:
    session = Session(bind=sync_conn)

    _seed_users(session)
    _seed_runner_configs(session)
    _seed_graph_definitions(session)
    _seed_task_executions(session)
    _seed_workflow_scenario(session)
    _seed_scheduler(session)
    _seed_projects(session)
    _seed_platform_events(session)

    session.commit()


# ──────────────────────────────────────────────────────────────────────────────
# User BC  — 3 users, each with 2 states + 2 skills, 4 sessions with states
# ──────────────────────────────────────────────────────────────────────────────


def _seed_users(session: Session) -> None:
    from shell.user_service.infrastructure.user.user.persistence.sql.models.user import UserModel
    from shell.user_service.infrastructure.user.user_skill.persistence.sql.models.user_skill import (
        UserSkillModel,
    )
    from shell.user_service.infrastructure.user.user_state.persistence.sql.models.user_state import (
        UserStateModel,
    )

    users_data = [
        {"id": f"{_DEV_ID_PREFIX}-user-alice", "email": "alice@example.com", "status": "active"},
        {"id": f"{_DEV_ID_PREFIX}-user-bob", "email": "bob@example.com", "status": "active"},
        {
            "id": f"{_DEV_ID_PREFIX}-user-charlie",
            "email": "charlie@example.com",
            "status": "inactive",
        },
    ]

    for ud in users_data:
        existing = session.execute(
            select(UserModel).where(UserModel.id == ud["id"])
        ).scalar_one_or_none()
        if existing is not None:
            continue

        user = UserModel(id=ud["id"], email=ud["email"], status=ud["status"], created_at=_NOW)
        session.add(user)

        for direction in ("INPUT", "OUTPUT"):
            session.add(
                UserStateModel(
                    id=f"{ud['id']}-state-{direction.lower()}",
                    user_id=ud["id"],
                    direction=direction,
                    state_data={"info": f"{direction.lower()} state for {ud['email']}"},
                    created_at=_NOW,
                )
            )

        for i in range(1, 3):
            level = "advanced" if i == 1 else "intermediate"
            session.add(
                UserSkillModel(
                    id=f"{ud['id']}-skill-{i}",
                    user_id=ud["id"],
                    skill_data={"name": f"skill-{i}", "level": level},
                    created_at=_NOW,
                )
            )

    _seed_sessions(session, users_data)


def _seed_sessions(session: Session, users_data: list[dict[str, Any]]) -> None:
    from shell.session_service.infrastructure.session.session.persistence.sql.models.session import (
        SessionModel,
    )
    from shell.session_service.infrastructure.session.session_state.persistence.sql.models.session_state import (
        SessionStateModel,
    )

    sessions_data = [
        {
            "id": f"{_DEV_ID_PREFIX}-session-alice-1",
            "user_id": users_data[0]["id"],
            "goal": "Refactor authentication module",
            "status": "open",
        },
        {
            "id": f"{_DEV_ID_PREFIX}-session-alice-2",
            "user_id": users_data[0]["id"],
            "goal": "Write API documentation",
            "status": "closed",
        },
        {
            "id": f"{_DEV_ID_PREFIX}-session-bob-1",
            "user_id": users_data[1]["id"],
            "goal": "Optimize database queries",
            "status": "open",
        },
        {
            "id": f"{_DEV_ID_PREFIX}-session-charlie-1",
            "user_id": users_data[2]["id"],
            "goal": "Review pull requests",
            "status": "open",
        },
    ]

    for sd in sessions_data:
        existing = session.execute(
            select(SessionModel).where(SessionModel.id == sd["id"])
        ).scalar_one_or_none()
        if existing is not None:
            continue

        is_closed = sd["status"] == "closed"
        sess = SessionModel(
            id=sd["id"],
            status=sd["status"],
            user_id=sd["user_id"],
            created_at=_NOW,
            opened_at=_NOW,
            closed_at=_NOW if is_closed else None,
        )
        session.add(sess)

        for direction in ("INPUT", "OUTPUT"):
            session.add(
                SessionStateModel(
                    id=f"{sd['id']}-state-{direction.lower()}",
                    session_id=sd["id"],
                    direction=direction,
                    state_data={"goal": sd["goal"], "step": direction.lower()},
                    created_at=_NOW,
                )
            )


# ──────────────────────────────────────────────────────────────────────────────
# Runner Configs  —  3 configs
# ──────────────────────────────────────────────────────────────────────────────


def _seed_runner_configs(session: Session) -> None:
    from shell.definition_service.infrastructure.definition.runner_config.persistence.sql.models.runner_config import (
        RunnerConfigModel,
    )

    configs = [
        RunnerConfigModel(
            id=f"{_DEV_ID_PREFIX}-runner-python",
            package_name="shell-runner-python",
            kind="python",
            hash="abc123def456",
            body={"entrypoint": "main.py", "interpreter": "python3.11"},
            created_at=_NOW,
        ),
        RunnerConfigModel(
            id=f"{_DEV_ID_PREFIX}-runner-shell",
            package_name="shell-runner-shell",
            kind="shell",
            hash="def789ghi012",
            body={"entrypoint": "run.sh", "shell": "bash"},
            created_at=_NOW,
        ),
        RunnerConfigModel(
            id=f"{_DEV_ID_PREFIX}-runner-node",
            package_name="shell-runner-node",
            kind="node",
            hash="jkl345mno678",
            body={"entrypoint": "index.js", "runtime": "node18"},
            created_at=_NOW,
        ),
    ]

    for c in configs:
        existing = session.execute(
            select(RunnerConfigModel).where(RunnerConfigModel.id == c.id)
        ).scalar_one_or_none()
        if existing is None:
            session.add(c)


# ──────────────────────────────────────────────────────────────────────────────
# Graph Definitions + Nodes + Transitions + Embeddings  —  3 graphs, 3-5 nodes
# ──────────────────────────────────────────────────────────────────────────────


def _seed_graph_definitions(session: Session) -> None:
    from shell.definition_service.infrastructure.definition.graph_definition.persistence.sql.models.graph_definition import (
        GraphDefinitionModel,
    )
    from shell.definition_service.infrastructure.definition.graph_definition_embedding.persistence.sql.models.graph_definition_embedding import (
        GraphDefinitionEmbeddingModel,
    )
    from shell.definition_service.infrastructure.definition.node_definition.persistence.sql.models.node_definition import (
        NodeDefinitionModel,
    )
    from shell.definition_service.infrastructure.definition.node_link_definition.persistence.sql.models.node_link_definition import (
        NodeLinkDefinitionModel,
    )

    # ── Graph 1: Simple Agent ────────────────────────────────────────────────
    g1 = GraphDefinitionModel(id=f"{_DEV_ID_PREFIX}-graph-simple-agent", created_at=_NOW)

    g1_nodes = [
        NodeDefinitionModel(
            id=f"{_DEV_ID_PREFIX}-gnode-agent-1",
            node_type="agent",
            max_step=10,
        ),
    ]
    g1_links = [
        NodeLinkDefinitionModel(
            id=f"{_DEV_ID_PREFIX}-glink-agent-1",
            graph_definition_id=g1.id,
            node_definition_id=g1_nodes[0].id,
        ),
    ]

    # ── Graph 2: Planner + Worker ────────────────────────────────────────────
    g2 = GraphDefinitionModel(id=f"{_DEV_ID_PREFIX}-graph-planner-worker", created_at=_NOW)

    g2_nodes = [
        NodeDefinitionModel(
            id=f"{_DEV_ID_PREFIX}-gnode-planner-1",
            node_type="planner",
            max_step=15,
        ),
        NodeDefinitionModel(
            id=f"{_DEV_ID_PREFIX}-gnode-worker-1",
            node_type="worker",
            max_step=20,
        ),
    ]
    g2_links = [
        NodeLinkDefinitionModel(
            id=f"{_DEV_ID_PREFIX}-glink-planner-1",
            graph_definition_id=g2.id,
            node_definition_id=g2_nodes[0].id,
        ),
        NodeLinkDefinitionModel(
            id=f"{_DEV_ID_PREFIX}-glink-worker-1",
            graph_definition_id=g2.id,
            node_definition_id=g2_nodes[1].id,
        ),
    ]

    # ── Graph 3: Full Pipeline ───────────────────────────────────────────────
    g3 = GraphDefinitionModel(id=f"{_DEV_ID_PREFIX}-graph-full-pipeline", created_at=_NOW)

    g3_nodes = [
        NodeDefinitionModel(
            id=f"{_DEV_ID_PREFIX}-gnode-tasker-1",
            node_type="tasker",
            max_step=20,
        ),
        NodeDefinitionModel(
            id=f"{_DEV_ID_PREFIX}-gnode-router-1",
            node_type="router",
            max_step=10,
        ),
        NodeDefinitionModel(
            id=f"{_DEV_ID_PREFIX}-gnode-agent-2",
            node_type="agent",
            max_step=15,
        ),
    ]
    g3_links = [
        NodeLinkDefinitionModel(
            id=f"{_DEV_ID_PREFIX}-glink-tasker-1",
            graph_definition_id=g3.id,
            node_definition_id=g3_nodes[0].id,
        ),
        NodeLinkDefinitionModel(
            id=f"{_DEV_ID_PREFIX}-glink-router-1",
            graph_definition_id=g3.id,
            node_definition_id=g3_nodes[1].id,
        ),
        NodeLinkDefinitionModel(
            id=f"{_DEV_ID_PREFIX}-glink-agent-2",
            graph_definition_id=g3.id,
            node_definition_id=g3_nodes[2].id,
        ),
    ]

    graphs_data: list[
        tuple[GraphDefinitionModel, list[NodeDefinitionModel], list[NodeLinkDefinitionModel]]
    ] = [
        (g1, g1_nodes, g1_links),
        (g2, g2_nodes, g2_links),
        (g3, g3_nodes, g3_links),
    ]

    for graph, nodes, links in graphs_data:
        existing = session.execute(
            select(GraphDefinitionModel).where(GraphDefinitionModel.id == graph.id)
        ).scalar_one_or_none()
        if existing is not None:
            continue

        session.add(graph)
        for node in nodes:
            session.add(node)
        for link in links:
            session.add(link)

        # Embedding for each graph
        session.add(
            GraphDefinitionEmbeddingModel(
                id=f"{graph.id}-embedding",
                graph_definition_id=graph.id,
                text=f"Embedding for {graph.id}",
                embedding=b"\x00\x01\x02",
                embedding_model="text-embedding-ada-002",
            )
        )


# ──────────────────────────────────────────────────────────────────────────────
# Task Executions  —  6 tasks (2 per workflow), each with INPUT/OUTPUT state
# ──────────────────────────────────────────────────────────────────────────────


def _seed_task_executions(session: Session) -> None:
    from shell.execution_service.infrastructure.execution.task_execution.persistence.sql.models.task_execution import (
        TaskExecutionModel,
    )
    from shell.execution_service.infrastructure.execution.task_execution_state.persistence.sql.models.task_execution_state import (
        TaskExecutionStateModel,
    )

    tasks: list[dict[str, Any]] = [
        {
            "model": TaskExecutionModel(
                id=f"{_DEV_ID_PREFIX}-task-simple-1",
                status="completed",
                name="simple-analysis-task",
                work_dir=f"{_DEV_ROOT}/simple/analysis",
                workflow_id=f"{_DEV_ID_PREFIX}-workflow-simple",
                created_at=_NOW,
            ),
            "input": {
                "description": "# Simple Analysis\nAnalyze the codebase.",
                "repo_url": "https://github.com/example/repo",
                "branch": "main",
            },
            "output": {"result": "success", "issues_found": 3},
        },
        {
            "model": TaskExecutionModel(
                id=f"{_DEV_ID_PREFIX}-task-simple-2",
                status="running",
                name="simple-fix-task",
                work_dir=f"{_DEV_ROOT}/simple/fix",
                workflow_id=f"{_DEV_ID_PREFIX}-workflow-simple",
                created_at=_NOW,
            ),
            "input": {"issue_ids": ["ISS-1", "ISS-2", "ISS-3"]},
            "output": {},
        },
        {
            "model": TaskExecutionModel(
                id=f"{_DEV_ID_PREFIX}-task-planner-1",
                status="completed",
                name="planner-design-task",
                work_dir=f"{_DEV_ROOT}/planner/design",
                workflow_id=f"{_DEV_ID_PREFIX}-workflow-planner",
                created_at=_NOW,
            ),
            "input": {"objective": "Design authentication module", "language": "python"},
            "output": {"design_doc": "/tmp/design.md", "approved": True},
        },
        {
            "model": TaskExecutionModel(
                id=f"{_DEV_ID_PREFIX}-task-planner-2",
                status="created",
                name="planner-implement-task",
                work_dir=f"{_DEV_ROOT}/planner/implement",
                workflow_id=f"{_DEV_ID_PREFIX}-workflow-planner",
                created_at=_NOW,
            ),
            "input": {"design_ref": "/tmp/design.md", "modules": ["auth", "session"]},
            "output": {},
        },
        {
            "model": TaskExecutionModel(
                id=f"{_DEV_ID_PREFIX}-task-pipeline-1",
                status="completed",
                name="pipeline-analysis-task",
                work_dir=f"{_DEV_ROOT}/pipeline/analysis",
                workflow_id=f"{_DEV_ID_PREFIX}-workflow-pipeline",
                created_at=_NOW,
            ),
            "input": {"project_path": f"{_DEV_ROOT}/project", "pipeline_stage": "analysis"},
            "output": {"requirements": ["req-1", "req-2"], "priority": "high"},
        },
        {
            "model": TaskExecutionModel(
                id=f"{_DEV_ID_PREFIX}-task-pipeline-2",
                status="running",
                name="pipeline-execute-task",
                work_dir=f"{_DEV_ROOT}/pipeline/execute",
                workflow_id=f"{_DEV_ID_PREFIX}-workflow-pipeline",
                created_at=_NOW,
            ),
            "input": {"stage": "build", "artifacts": ["src/", "tests/"]},
            "output": {},
        },
    ]

    for t in tasks:
        existing = session.execute(
            select(TaskExecutionModel).where(TaskExecutionModel.id == t["model"].id)
        ).scalar_one_or_none()
        if existing is not None:
            continue

        session.add(t["model"])

        session.add(
            TaskExecutionStateModel(
                id=f"{t['model'].id}-input",
                task_execution_id=t["model"].id,
                direction="INPUT",
                state_data=t["input"],
                created_at=_NOW,
            )
        )

        if t["output"]:
            session.add(
                TaskExecutionStateModel(
                    id=f"{t['model'].id}-output",
                    task_execution_id=t["model"].id,
                    direction="OUTPUT",
                    state_data=t["output"],
                    created_at=_NOW,
                )
            )


# ──────────────────────────────────────────────────────────────────────────────
# Workflow Scenario  —  3 workflows with full execution hierarchy (~2 tasks each)
# ──────────────────────────────────────────────────────────────────────────────


def _seed_workflow_scenario(session: Session) -> None:
    from shell.execution_service.infrastructure.execution.agent_config_execution.persistence.sql.models.agent_config_execution import (
        AgentConfigExecutionModel,
    )
    from shell.execution_service.infrastructure.execution.agent_execution.persistence.sql.models.agent_execution import (
        AgentExecutionModel,
    )
    from shell.execution_service.infrastructure.execution.agent_skill_execution.persistence.sql.models.agent_skill_execution import (
        AgentSkillExecutionModel,
    )
    from shell.execution_service.infrastructure.execution.edge_execution.persistence.sql.models.edge_execution import (
        EdgeExecutionModel,
    )
    from shell.execution_service.infrastructure.execution.edge_link_execution.persistence.sql.models.edge_link_execution import (
        EdgeLinkExecutionModel,
    )
    from shell.execution_service.infrastructure.execution.graph_execution.persistence.sql.models.graph_execution import (
        GraphExecutionModel,
    )
    from shell.execution_service.infrastructure.execution.graph_execution_state.persistence.sql.models.graph_execution_state import (
        GraphExecutionStateModel,
    )
    from shell.execution_service.infrastructure.execution.node_execution.persistence.sql.models.node_execution import (
        NodeExecutionModel,
    )
    from shell.execution_service.infrastructure.execution.node_execution.persistence.sql.models.node_execution_result import (
        NodeExecutionResultModel,
    )
    from shell.execution_service.infrastructure.execution.node_execution_state.persistence.sql.models.node_execution_state_aggregate import (
        NodeExecutionStateModel,
    )
    from shell.execution_service.infrastructure.execution.node_link_execution.persistence.sql.models.node_link_execution import (
        NodeLinkExecutionModel,
    )
    from shell.execution_service.infrastructure.execution.session_execution.persistence.sql.models.session_execution import (
        SessionExecutionModel,
    )
    from shell.execution_service.infrastructure.execution.session_execution_state.persistence.sql.models.session_execution_state import (
        SessionExecutionStateModel,
    )
    from shell.execution_service.infrastructure.execution.user_execution.persistence.sql.models.user_execution import (
        UserExecutionModel,
    )
    from shell.execution_service.infrastructure.execution.user_execution_state.persistence.sql.models.user_execution_state import (
        UserExecutionStateModel,
    )
    from shell.execution_service.infrastructure.execution.workflow.persistence.sql.models.workflow import (
        WorkflowModel,
    )

    workflows_data: list[dict[str, Any]] = [
        {
            "id": f"{_DEV_ID_PREFIX}-workflow-simple",
            "status": "done",
            "session_id": f"{_DEV_ID_PREFIX}-session-alice-1",
            "graph_def_id": f"{_DEV_ID_PREFIX}-graph-simple-agent",
            "task_ids": [f"{_DEV_ID_PREFIX}-task-simple-1", f"{_DEV_ID_PREFIX}-task-simple-2"],
        },
        {
            "id": f"{_DEV_ID_PREFIX}-workflow-planner",
            "status": "running",
            "session_id": f"{_DEV_ID_PREFIX}-session-bob-1",
            "graph_def_id": f"{_DEV_ID_PREFIX}-graph-planner-worker",
            "task_ids": [f"{_DEV_ID_PREFIX}-task-planner-1", f"{_DEV_ID_PREFIX}-task-planner-2"],
        },
        {
            "id": f"{_DEV_ID_PREFIX}-workflow-pipeline",
            "status": "idle",
            "session_id": f"{_DEV_ID_PREFIX}-session-charlie-1",
            "graph_def_id": f"{_DEV_ID_PREFIX}-graph-full-pipeline",
            "task_ids": [f"{_DEV_ID_PREFIX}-task-pipeline-1", f"{_DEV_ID_PREFIX}-task-pipeline-2"],
        },
    ]

    for wd in workflows_data:
        existing = session.execute(
            select(WorkflowModel).where(WorkflowModel.id == wd["id"])
        ).scalar_one_or_none()
        if existing is not None:
            continue

        wf = WorkflowModel(
            id=wd["id"],
            status=wd["status"],
            session_id=wd["session_id"],
            created_at=_NOW,
        )
        session.add(wf)

        # UserExecution + SessionExecution per workflow
        wf_user_id = wd["session_id"].replace("-session-", "-user-")
        user_exec_id = f"{wd['id']}-user-exec"
        session_exec_id = f"{wd['id']}-session-exec"

        existing_ue = session.execute(
            select(UserExecutionModel).where(UserExecutionModel.id == user_exec_id)
        ).scalar_one_or_none()
        if existing_ue is None:
            ue = UserExecutionModel(id=user_exec_id, user_id=wf_user_id, created_at=_NOW)
            session.add(ue)
            for direction in ("INPUT", "OUTPUT"):
                session.add(
                    UserExecutionStateModel(
                        id=f"{user_exec_id}-state-{direction.lower()}",
                        user_execution_id=user_exec_id,
                        direction=direction,
                        state_data={"workflow_id": wd["id"], "action": direction.lower()},
                        created_at=_NOW,
                    )
                )

            se = SessionExecutionModel(
                id=session_exec_id,
                user_execution_id=user_exec_id,
                session_id=wd["session_id"],
                created_at=_NOW,
            )
            session.add(se)
            for direction in ("INPUT", "OUTPUT"):
                session.add(
                    SessionExecutionStateModel(
                        id=f"{session_exec_id}-state-{direction.lower()}",
                        session_execution_id=session_exec_id,
                        direction=direction,
                        state_data={"workflow_id": wd["id"], "step": direction.lower()},
                        created_at=_NOW,
                    )
                )

        # ── Graph Execution per task ──────────────────────────────────────────
        for task_idx, task_id in enumerate(wd["task_ids"]):
            ge_id = f"{wd['id']}-ge-{task_idx}"
            tags = {
                "workflow": wd["id"],
                "task": task_id,
                "env": "dev",
                "priority": "normal",
            }

            ge = GraphExecutionModel(
                id=ge_id,
                task_execution_id=task_id,
                graph_definition_id=wd["graph_def_id"],
                status="completed" if task_idx == 0 else "running",
                parent_graph_execution_id=None,
                state_input={"task": task_id},
                state_output={"result": "ok"} if task_idx == 0 else {},
                depth=0,
                timeout_at=None,
                correlation_id=f"corr-{wd['id']}-{task_idx}",
                tags=tags,
            )
            session.add(ge)

            session.add(
                GraphExecutionStateModel(
                    id=f"{ge_id}-state-input",
                    graph_execution_id=ge_id,
                    direction="INPUT",
                    state_data={"task_id": task_id, "mode": "auto"},
                    created_at=_NOW,
                )
            )
            session.add(
                GraphExecutionStateModel(
                    id=f"{ge_id}-state-output",
                    graph_execution_id=ge_id,
                    direction="OUTPUT",
                    state_data={"status": "completed", "message": "Done"},
                    created_at=_NOW,
                )
            )

            # ── Node Executions ──────────────────────────────────────────────
            if wd["graph_def_id"] == f"{_DEV_ID_PREFIX}-graph-simple-agent":
                node_defs = [
                    {
                        "id": f"{_DEV_ID_PREFIX}-gnode-agent-1",
                        "mode": "agent",
                        "role": "agent",
                        "node_type": "agent",
                    },
                ]
            elif wd["graph_def_id"] == f"{_DEV_ID_PREFIX}-graph-planner-worker":
                node_defs = [
                    {
                        "id": f"{_DEV_ID_PREFIX}-gnode-planner-1",
                        "mode": "planner",
                        "role": "planner",
                        "node_type": "planner",
                    },
                    {
                        "id": f"{_DEV_ID_PREFIX}-gnode-worker-1",
                        "mode": "worker",
                        "role": "worker",
                        "node_type": "worker",
                    },
                ]
            else:
                node_defs = [
                    {
                        "id": f"{_DEV_ID_PREFIX}-gnode-tasker-1",
                        "mode": "tasker",
                        "role": "tasker",
                        "node_type": "tasker",
                    },
                    {
                        "id": f"{_DEV_ID_PREFIX}-gnode-router-1",
                        "mode": "router",
                        "role": "router",
                        "node_type": "router",
                    },
                    {
                        "id": f"{_DEV_ID_PREFIX}-gnode-agent-2",
                        "mode": "agent",
                        "role": "agent",
                        "node_type": "agent",
                    },
                ]

            for pos, nd in enumerate(node_defs):
                gne_id = f"{ge_id}-node-{pos}"

                gne = NodeExecutionModel(
                    id=gne_id,
                    position=pos,
                    mode=nd["mode"],
                    role=nd["role"],
                    node_type=nd["node_type"],
                    model="gpt-4",
                    command="",
                    retries=1,
                    log_level="INFO",
                    max_step=10,
                    no_ask_user=False,
                    autopilot=True,
                    task_execution_id=task_id,
                    source_dir=f"{_DEV_ROOT}/{nd['mode']}",
                    status="completed" if task_idx == 0 else "pending",
                    status_initial="",
                )
                session.add(gne)

                # NodeLink
                session.add(
                    NodeLinkExecutionModel(
                        id=f"{ge_id}-{gne_id}",
                        graph_execution_id=ge_id,
                        node_execution_id=gne_id,
                    )
                )

                # NodeState
                for direction in ("INPUT", "OUTPUT"):
                    session.add(
                        NodeExecutionStateModel(
                            id=f"{gne_id}-state-{direction.lower()}",
                            node_execution_id=gne_id,
                            direction=direction,
                            state_data={
                                "mode": nd["mode"],
                                "position": pos,
                                "step": direction.lower(),
                            },
                            created_at=_NOW,
                        )
                    )

                # NodeResult (only for completed tasks)
                if task_idx == 0:
                    session.add(
                        NodeExecutionResultModel(
                            id=f"{gne_id}-result",
                            node_execution_id=gne_id,
                            workflow_id=wd["id"],
                            status="completed",
                            stdout=f"[{nd['mode']}] Task completed successfully.\nPosition: {pos}",
                            stderr="",
                            artifact_uri=f"file://{_DEV_ROOT}/results/{nd['mode']}-{pos}.json",
                            created_at=_NOW,
                        )
                    )

                # AgentExecution for agent-type nodes
                if nd["node_type"] == "agent":
                    agent_exec_id = f"{gne_id}-agent-exec"
                    session.add(
                        AgentExecutionModel(
                            id=agent_exec_id,
                            node_execution_id=gne_id,
                            created_at=_NOW,
                            changed_at=_NOW,
                        )
                    )
                    session.add(
                        AgentConfigExecutionModel(
                            id=f"{agent_exec_id}-config",
                            agent_execution_id=agent_exec_id,
                            config_data='{"model": "gpt-4", "temperature": 0.7, "max_tokens": 2048, "top_p": 0.9}',
                            created_at=_NOW,
                        )
                    )
                    for skill_idx in range(1, 3):
                        session.add(
                            AgentSkillExecutionModel(
                                id=f"{agent_exec_id}-skill-{skill_idx}",
                                agent_execution_id=agent_exec_id,
                                skill_data={
                                    "name": f"agent-skill-{skill_idx}",
                                    "category": "coding" if skill_idx == 1 else "analysis",
                                },
                                created_at=_NOW,
                            )
                        )

            # Edge Execution (1 per graph execution)
            edge_id = f"{ge_id}-edge-0"
            session.add(
                EdgeExecutionModel(
                    id=edge_id,
                    edge_definition_id=f"{wd['graph_def_id']}-edge-def-0",
                    source_node_execution_id=f"{ge_id}-node-0",
                    target_node_execution_id=f"{ge_id}-node-1" if len(node_defs) > 1 else None,
                    created_at=_NOW,
                    changed_at=_NOW,
                )
            )
            session.add(
                EdgeLinkExecutionModel(
                    id=f"{edge_id}-link-0",
                    node_execution_id=f"{ge_id}-node-0",
                    edge_execution_id=edge_id,
                    created_at=_NOW,
                    changed_at=_NOW,
                )
            )


# ──────────────────────────────────────────────────────────────────────────────
# Scheduler  —  3 definitions, each with 1 execution
# ──────────────────────────────────────────────────────────────────────────────


def _seed_scheduler(session: Session) -> None:
    from shell.scheduling_service.infrastructure.scheduling.scheduler_definition.persistence.sql.models.scheduler_definition import (
        SchedulerDefinitionModel,
    )
    from shell.scheduling_service.infrastructure.scheduling.scheduler_execution.persistence.sql.models.scheduler_execution import (
        SchedulerExecutionModel,
    )

    definitions_data: list[dict[str, Any]] = [
        {
            "id": f"{_DEV_ID_PREFIX}-scheduler-outbox-relay",
            "name": "outbox-relay",
            "description": "Processes pending outbox events and publishes them to inbox",
            "source_context": "platform",
            "trigger_event_type": "OutboxPollingEvent",
            "trigger_filter": {"event_types": ["*"]},
            "action_type": "relay",
            "action_config": {"batch_size": 100, "max_retries": 3, "target": "outbox_to_inbox"},
            "execution_policy": {
                "max_concurrent": 1,
                "timeout_seconds": 60,
                "retry_policy": {"max_attempts": 3, "backoff_seconds": 5},
            },
        },
        {
            "id": f"{_DEV_ID_PREFIX}-scheduler-cleanup",
            "name": "cleanup-stale",
            "description": "Cleans up stale executions and state records",
            "source_context": "execution",
            "trigger_event_type": "CleanupEvent",
            "trigger_filter": {"age_hours": 72},
            "action_type": "cleanup",
            "action_config": {"batch_size": 500, "retention_hours": 168},
            "execution_policy": {"max_concurrent": 1, "timeout_seconds": 300},
        },
        {
            "id": f"{_DEV_ID_PREFIX}-scheduler-health",
            "name": "health-check",
            "description": "Periodic health check for all active sessions",
            "source_context": "session",
            "trigger_event_type": "HealthCheckEvent",
            "trigger_filter": {},
            "action_type": "monitor",
            "action_config": {"check_interval": 60, "timeout_threshold": 300},
            "execution_policy": {"max_concurrent": 5, "timeout_seconds": 30},
        },
    ]

    for dd in definitions_data:
        existing_def = session.execute(
            select(SchedulerDefinitionModel).where(SchedulerDefinitionModel.id == dd["id"])
        ).scalar_one_or_none()

        if existing_def is None:
            definition = SchedulerDefinitionModel(
                id=dd["id"],
                name=dd["name"],
                description=dd["description"],
                source_context=dd["source_context"],
                trigger_event_type=dd["trigger_event_type"],
                trigger_filter=dd["trigger_filter"],
                action_type=dd["action_type"],
                action_config=dd["action_config"],
                execution_policy=dd["execution_policy"],
                enabled=True,
                created_at=_NOW,
                changed_at=_NOW,
            )
            session.add(definition)

        try:
            exec_id = f"{dd['id']}-exec"
            existing_exec = session.execute(
                select(SchedulerExecutionModel).where(SchedulerExecutionModel.id == exec_id)
            ).scalar_one_or_none()

            if existing_exec is None:
                execution = SchedulerExecutionModel(
                    id=exec_id,
                    scheduler_definition_id=dd["id"],
                    name=f"{dd['name']}-executor",
                    job_type=dd["source_context"],
                    interval_seconds=10.0,
                    batch_size=dd["action_config"].get("batch_size", 50),
                    enabled=True,
                    config={"poll_interval": 10, **dd["action_config"]},
                    created_at=_NOW,
                    changed_at=_NOW,
                )
                session.add(execution)
        except Exception:
            pass  # Schema mismatch — non-critical for dev seed data


# ──────────────────────────────────────────────────────────────────────────────
# Projects  —  3 projects, each with 2 states + 1 skill
# ──────────────────────────────────────────────────────────────────────────────


def _seed_projects(session: Session) -> None:
    from shell.project_service.infrastructure.project.project.persistence.sql.models.project import (
        ProjectModel,
    )
    from shell.project_service.infrastructure.project.project_skill.persistence.sql.models.project_skill import (
        ProjectSkillModel,
    )
    from shell.project_service.infrastructure.project.project_state.persistence.sql.models.project_state import (
        ProjectStateModel,
    )

    projects_data: list[dict[str, Any]] = [
        {
            "id": f"{_DEV_ID_PREFIX}-project-alpha",
            "name": "Alpha",
            "repo_url": "https://github.com/example/alpha",
            "status": "active",
        },
        {
            "id": f"{_DEV_ID_PREFIX}-project-beta",
            "name": "Beta",
            "repo_url": "https://github.com/example/beta",
            "status": "active",
        },
        {
            "id": f"{_DEV_ID_PREFIX}-project-gamma",
            "name": "Gamma",
            "repo_url": None,
            "status": "archived",
        },
    ]

    for pd in projects_data:
        existing = session.execute(
            select(ProjectModel).where(ProjectModel.id == pd["id"])
        ).scalar_one_or_none()
        if existing is not None:
            continue

        project = ProjectModel(
            id=pd["id"],
            name=pd["name"],
            repo_url=pd["repo_url"],
            status=pd["status"],
            created_at=_NOW,
        )
        session.add(project)

        for direction in ("INPUT", "OUTPUT"):
            session.add(
                ProjectStateModel(
                    id=f"{pd['id']}-state-{direction.lower()}",
                    project_id=pd["id"],
                    direction=direction,
                    state_data={"name": pd["name"], "phase": direction.lower()},
                    created_at=_NOW,
                )
            )

        skill_name = "python-dev" if pd["status"] == "active" else "legacy-maintenance"
        skill_level = "expert" if pd["status"] == "active" else "intermediate"
        session.add(
            ProjectSkillModel(
                id=f"{pd['id']}-skill-1",
                project_id=pd["id"],
                skill_data={"name": skill_name, "level": skill_level},
                created_at=_NOW,
            )
        )


# ──────────────────────────────────────────────────────────────────────────────
# Platform Events  —  audit (5) + outbox (3) + inbox (3)
# ──────────────────────────────────────────────────────────────────────────────


def _seed_platform_events(session: Session) -> None:
    from shell.ingestion_service.infrastructure.ingestion.persistence.sql.models.base import (
        PERSISTENCE_DELIVERY_MODELS,
    )

    _AUDIT_MODEL: Any = PERSISTENCE_DELIVERY_MODELS.audit
    _INBOX_MODEL: Any = PERSISTENCE_DELIVERY_MODELS.events.inbox
    _OUTBOX_MODEL: Any = PERSISTENCE_DELIVERY_MODELS.events.outbox

    # Audit events
    audit_events = [
        _AUDIT_MODEL(
            id=f"{_DEV_ID_PREFIX}-audit-1",
            event_type="user.login",
            occurred_at=_NOW,
            payload={"user_id": f"{_DEV_ID_PREFIX}-user-alice", "ip": "192.168.1.10"},
        ),
        _AUDIT_MODEL(
            id=f"{_DEV_ID_PREFIX}-audit-2",
            event_type="workflow.created",
            occurred_at=_NOW,
            payload={
                "workflow_id": f"{_DEV_ID_PREFIX}-workflow-simple",
                "session_id": f"{_DEV_ID_PREFIX}-session-alice-1",
            },
        ),
        _AUDIT_MODEL(
            id=f"{_DEV_ID_PREFIX}-audit-3",
            event_type="task.completed",
            occurred_at=_NOW,
            payload={"task_id": f"{_DEV_ID_PREFIX}-task-simple-1", "status": "completed"},
        ),
        _AUDIT_MODEL(
            id=f"{_DEV_ID_PREFIX}-audit-4",
            event_type="scheduler.triggered",
            occurred_at=_NOW,
            payload={"scheduler_id": f"{_DEV_ID_PREFIX}-scheduler-outbox-relay", "action": "relay"},
        ),
        _AUDIT_MODEL(
            id=f"{_DEV_ID_PREFIX}-audit-5",
            event_type="project.archived",
            occurred_at=_NOW,
            payload={"project_id": f"{_DEV_ID_PREFIX}-project-gamma", "reason": "completed"},
        ),
    ]
    for evt in audit_events:
        existing = session.execute(
            select(_AUDIT_MODEL).where(_AUDIT_MODEL.id == evt.id)
        ).scalar_one_or_none()
        if existing is None:
            session.add(evt)

    # Outbox events
    outbox_events = [
        _OUTBOX_MODEL(
            id=f"{_DEV_ID_PREFIX}-outbox-1",
            event_type="workflow.completed",
            occurred_at=_NOW,
            payload={"workflow_id": f"{_DEV_ID_PREFIX}-workflow-simple"},
            correlation_id="corr-outbox-1",
            causation_id="cause-outbox-1",
            published_at=None,
        ),
        _OUTBOX_MODEL(
            id=f"{_DEV_ID_PREFIX}-outbox-2",
            event_type="task.created",
            occurred_at=_NOW,
            payload={"task_id": f"{_DEV_ID_PREFIX}-task-planner-2"},
            correlation_id="corr-outbox-2",
            causation_id="cause-outbox-2",
            published_at=None,
        ),
        _OUTBOX_MODEL(
            id=f"{_DEV_ID_PREFIX}-outbox-3",
            event_type="workflow.started",
            occurred_at=_NOW,
            payload={"workflow_id": f"{_DEV_ID_PREFIX}-workflow-pipeline"},
            correlation_id="corr-outbox-3",
            causation_id="cause-outbox-3",
            published_at=_NOW,
        ),
    ]
    for outbox_evt in outbox_events:
        outbox_existing = session.execute(
            select(_OUTBOX_MODEL).where(_OUTBOX_MODEL.id == outbox_evt.id)
        ).scalar_one_or_none()
        if outbox_existing is None:
            session.add(outbox_evt)

    # Inbox events
    inbox_events = [
        _INBOX_MODEL(
            id=f"{_DEV_ID_PREFIX}-inbox-1",
            event_type="workflow.completed",
            occurred_at=_NOW,
            payload={"workflow_id": f"{_DEV_ID_PREFIX}-workflow-simple"},
            correlation_id="corr-inbox-1",
            causation_id="cause-inbox-1",
            received_at=_NOW,
            processed_at=None,
        ),
        _INBOX_MODEL(
            id=f"{_DEV_ID_PREFIX}-inbox-2",
            event_type="task.created",
            occurred_at=_NOW,
            payload={"task_id": f"{_DEV_ID_PREFIX}-task-planner-2"},
            correlation_id="corr-inbox-2",
            causation_id="cause-inbox-2",
            received_at=_NOW,
            processed_at=_NOW,
        ),
        _INBOX_MODEL(
            id=f"{_DEV_ID_PREFIX}-inbox-3",
            event_type="scheduler.ready",
            occurred_at=_NOW,
            payload={"scheduler_id": f"{_DEV_ID_PREFIX}-scheduler-health"},
            correlation_id="corr-inbox-3",
            causation_id="cause-inbox-3",
            received_at=_NOW,
            processed_at=None,
        ),
    ]
    for inbox_evt in inbox_events:
        inbox_existing = session.execute(
            select(_INBOX_MODEL).where(_INBOX_MODEL.id == inbox_evt.id)
        ).scalar_one_or_none()
        if inbox_existing is None:
            session.add(inbox_evt)


# ──────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed development data into database")
    parser.add_argument(
        "--url",
        default=os.environ.get("SHELL_DATABASE_URL", "sqlite+aiosqlite:///shell_dev.db"),
        help="Database URL (default: SHELL_DATABASE_URL env or sqlite+aiosqlite:///shell_dev.db)",
    )
    args = parser.parse_args()

    import asyncio

    asyncio.run(seed_dev_data(args.url))
    print(f"Dev seed data loaded into {args.url}")


if __name__ == "__main__":
    main()
