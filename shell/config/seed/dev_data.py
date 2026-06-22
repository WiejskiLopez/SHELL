"""Dev seed data — comprehensive test data for local development.

Creates realistic sample RunnerConfigs, GraphDefinitions (with nodes
and transitions), TaskExecutions, Workflows, Envelopes, Results, and Schedulers.

Only invoked when seed_dev_data is enabled (dev profile or SHELL_SEED_DEV_DATA=true).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

_DEV_ID_PREFIX = "dev"

_NOW = datetime.now(tz=UTC)


async def seed_dev_data(url: str) -> None:
    """Seed comprehensive development data into the database."""
    engine = create_async_engine(url, echo=False, future=True)

    async with engine.begin() as conn:
        await conn.run_sync(_seed_dev_sync)

    await engine.dispose()


def _seed_dev_sync(sync_conn) -> None:
    from sqlalchemy.orm import Session

    session = Session(sync_conn)

    _seed_runner_configs(session)
    _seed_graph_definitions(session)
    _seed_task_executions(session)
    _seed_workflow_scenario(session)
    _seed_scheduler(session)

    session.commit()


# ──────────────────────────────────────────────────────────────────────────────
# Runner Configs
# ──────────────────────────────────────────────────────────────────────────────


def _seed_runner_configs(session: Session) -> None:
    from shell.infrastructure.definition.persistence.sql.models.runner_config import (
        RunnerConfigModel,
    )

    configs = [
        RunnerConfigModel(
            id=f"{_DEV_ID_PREFIX}-runner-python",
            package_name="python-runner",
            kind="subprocess",
            hash="sha256:py-runner-v1",
            body={
                "runtime": "python3.11",
                "entrypoint": "main.py",
                "env": {"PYTHONUNBUFFERED": "1"},
                "timeout_seconds": 300,
                "max_retries": 2,
            },
            created_at=_NOW,
        ),
        RunnerConfigModel(
            id=f"{_DEV_ID_PREFIX}-runner-shell",
            package_name="shell-runner",
            kind="subprocess",
            hash="sha256:sh-runner-v1",
            body={
                "runtime": "bash",
                "entrypoint": "run.sh",
                "env": {"SHELL": "/bin/bash"},
                "timeout_seconds": 120,
                "max_retries": 0,
            },
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
# Graph Definitions + Nodes + Transitions
# ──────────────────────────────────────────────────────────────────────────────


def _seed_graph_definitions(session: Session) -> None:
    from shell.infrastructure.definition.persistence.sql.models.graph_definition import (
        GraphDefinitionModel,
    )
    from shell.infrastructure.definition.persistence.sql.models.graph_node_definition import (
        GraphNodeDefinitionModel,
    )
    from shell.infrastructure.definition.persistence.sql.models.graph_node_transition_definition import (
        GraphNodeTransitionDefinitionModel,
    )

    # ── Graph 1: Simple Agent ────────────────────────────────────────────────
    g1 = GraphDefinitionModel(
        id=f"{_DEV_ID_PREFIX}-graph-simple-agent",
        name="simple-agent",
        purpose="Single agent node that executes autonomously",
    )

    g1_node_1 = GraphNodeDefinitionModel(
        id=f"{_DEV_ID_PREFIX}-gnode-agent-1",
        graph_definition_id=g1.id,
        position=0,
        mode="agent",
        role="agent",
        node_type="agent",
        model="gpt-4",
        command="",
        timeout=120,
        retries=1,
        log_level="INFO",
        max_step=10,
        no_ask_user=False,
        autopilot=True,
        status_initial="idle",
        script=None,
        script_type=None,
    )

    # ── Graph 2: Planner → Worker ────────────────────────────────────────────
    g2 = GraphDefinitionModel(
        id=f"{_DEV_ID_PREFIX}-graph-planner-worker",
        name="planner-worker",
        purpose="Two-node pipeline: planner creates a plan, worker executes it",
    )

    g2_node_1 = GraphNodeDefinitionModel(
        id=f"{_DEV_ID_PREFIX}-gnode-planner-1",
        graph_definition_id=g2.id,
        position=0,
        mode="planner",
        role="planner",
        node_type="planner",
        model="gpt-4",
        command="",
        timeout=180,
        retries=1,
        log_level="INFO",
        max_step=15,
        no_ask_user=False,
        autopilot=True,
        status_initial="idle",
        script=None,
        script_type=None,
    )

    g2_node_2 = GraphNodeDefinitionModel(
        id=f"{_DEV_ID_PREFIX}-gnode-worker-1",
        graph_definition_id=g2.id,
        position=1,
        mode="worker",
        role="worker",
        node_type="worker",
        model="",
        command="",
        timeout=300,
        retries=2,
        log_level="INFO",
        max_step=20,
        no_ask_user=True,
        autopilot=True,
        status_initial="idle",
        script=None,
        script_type=None,
    )

    g2_transition_1 = GraphNodeTransitionDefinitionModel(
        id=f"{_DEV_ID_PREFIX}-gtransition-planner-to-worker",
        graph_definition_id=g2.id,
        source_node_definition_id=g2_node_1.id,
        target_node_definition_id=g2_node_2.id,
        transition_type="sequence",
        priority=0,
        condition_expression=None,
        condition_language=None,
        join_wait_count=None,
        max_loop_count=0,
        timeout_seconds=None,
        retry_count=0,
        retry_delay_seconds=0,
        data_mapping=None,
        label="planner -> worker",
        created_at=_NOW,
        updated_at=_NOW,
    )

    # ── Graph 3: Full Pipeline (Tasker → Router → Agent) ────────────────────
    g3 = GraphDefinitionModel(
        id=f"{_DEV_ID_PREFIX}-graph-full-pipeline",
        name="full-pipeline",
        purpose="Three-node pipeline: tasker delegates, router directs, agent acts",
    )

    g3_node_1 = GraphNodeDefinitionModel(
        id=f"{_DEV_ID_PREFIX}-gnode-tasker-1",
        graph_definition_id=g3.id,
        position=0,
        mode="tasker",
        role="tasker",
        node_type="tasker",
        model="gpt-4",
        command="",
        timeout=180,
        retries=1,
        log_level="INFO",
        max_step=20,
        no_ask_user=False,
        autopilot=True,
        status_initial="idle",
        script=None,
        script_type=None,
    )

    g3_node_2 = GraphNodeDefinitionModel(
        id=f"{_DEV_ID_PREFIX}-gnode-router-1",
        graph_definition_id=g3.id,
        position=1,
        mode="router",
        role="router",
        node_type="router",
        model="gpt-4",
        command="",
        timeout=120,
        retries=1,
        log_level="INFO",
        max_step=10,
        no_ask_user=False,
        autopilot=False,
        status_initial="idle",
        script=None,
        script_type=None,
    )

    g3_node_3 = GraphNodeDefinitionModel(
        id=f"{_DEV_ID_PREFIX}-gnode-agent-2",
        graph_definition_id=g3.id,
        position=2,
        mode="agent",
        role="agent",
        node_type="agent",
        model="gpt-4",
        command="",
        timeout=240,
        retries=2,
        log_level="INFO",
        max_step=15,
        no_ask_user=False,
        autopilot=True,
        status_initial="idle",
        script=None,
        script_type=None,
    )

    g3_transition_1 = GraphNodeTransitionDefinitionModel(
        id=f"{_DEV_ID_PREFIX}-gtransition-tasker-to-router",
        graph_definition_id=g3.id,
        source_node_definition_id=g3_node_1.id,
        target_node_definition_id=g3_node_2.id,
        transition_type="sequence",
        priority=0,
        condition_expression=None,
        condition_language=None,
        join_wait_count=None,
        max_loop_count=0,
        timeout_seconds=None,
        retry_count=0,
        retry_delay_seconds=0,
        data_mapping=None,
        label="tasker -> router",
        created_at=_NOW,
        updated_at=_NOW,
    )

    g3_transition_2 = GraphNodeTransitionDefinitionModel(
        id=f"{_DEV_ID_PREFIX}-gtransition-router-to-agent",
        graph_definition_id=g3.id,
        source_node_definition_id=g3_node_2.id,
        target_node_definition_id=g3_node_3.id,
        transition_type="sequence",
        priority=0,
        condition_expression=None,
        condition_language=None,
        join_wait_count=None,
        max_loop_count=0,
        timeout_seconds=None,
        retry_count=0,
        retry_delay_seconds=0,
        data_mapping=None,
        label="router -> agent",
        created_at=_NOW,
        updated_at=_NOW,
    )

    # ── Persist (check existence first) ──────────────────────────────────────
    graphs_data = [
        (g1, [g1_node_1], []),
        (g2, [g2_node_1, g2_node_2], [g2_transition_1]),
        (g3, [g3_node_1, g3_node_2, g3_node_3], [g3_transition_1, g3_transition_2]),
    ]

    for graph, nodes, transitions in graphs_data:
        existing = session.execute(
            select(GraphDefinitionModel).where(GraphDefinitionModel.id == graph.id)
        ).scalar_one_or_none()
        if existing is not None:
            continue
        session.add(graph)
        for node in nodes:
            session.add(node)
        for tr in transitions:
            session.add(tr)


# ──────────────────────────────────────────────────────────────────────────────
# Task Executions + Input/Output Payloads
# ──────────────────────────────────────────────────────────────────────────────


def _seed_task_executions(session: Session) -> None:
    from shell.infrastructure.execution.persistence.sql.models.task_execution import (
        TaskExecutionModel,
    )
    from shell.infrastructure.execution.persistence.sql.models.task_execution_state_input import (
        TaskExecutionStateInputModel,
    )
    from shell.infrastructure.execution.persistence.sql.models.task_execution_state_output import (
        TaskExecutionStateOutputModel,
    )

    tasks: list[dict[str, Any]] = [
        {
            "model": TaskExecutionModel(
                id=f"{_DEV_ID_PREFIX}-task-simple-agent",
                status="CREATED",
                name="dev-simple-agent-task",
                work_dir="/tmp/shell/dev/simple-agent",
                workflow_id=None,
                created_at=_NOW,
            ),
            "input_payload": {
                "description": "# Simple Agent Task\nExecute autonomously.",
                "repo_url": "https://github.com/example/repo",
                "branch": "main",
            },
            "output_payload": {},  # not yet executed
        },
        {
            "model": TaskExecutionModel(
                id=f"{_DEV_ID_PREFIX}-task-planner-worker",
                status="CREATED",
                name="dev-planner-worker-task",
                work_dir="/tmp/shell/dev/planner-worker",
                workflow_id=None,
                created_at=_NOW,
            ),
            "input_payload": {
                "description": "# Planner Worker Task\nPlan and execute.",
                "objective": "Refactor authentication module",
                "language": "python",
            },
            "output_payload": {},
        },
        {
            "model": TaskExecutionModel(
                id=f"{_DEV_ID_PREFIX}-task-full-pipeline",
                status="CREATED",
                name="dev-full-pipeline-task",
                work_dir="/tmp/shell/dev/full-pipeline",
                workflow_id=None,
                created_at=_NOW,
            ),
            "input_payload": {
                "description": "# Full Pipeline Task\nEnd-to-end orchestration.",
                "project_path": "/tmp/shell/dev/project",
                "pipeline_stage": "analysis",
            },
            "output_payload": {},
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
            TaskExecutionStateInputModel(
                id=f"{t['model'].id}-input",
                task_execution_id=t["model"].id,
                payload=t["input_payload"],
                is_current=True,
                created_at=_NOW,
            )
        )
        if t["output_payload"]:
            session.add(
                TaskExecutionStateOutputModel(
                    id=f"{t['model'].id}-output",
                    task_execution_id=t["model"].id,
                    payload=t["output_payload"],
                    is_current=True,
                    created_at=_NOW,
                )
            )


# ──────────────────────────────────────────────────────────────────────────────
# Workflow Scenario — full execution with envelopes and results
# ──────────────────────────────────────────────────────────────────────────────


def _seed_workflow_scenario(session: Session) -> None:
    from shell.infrastructure.execution.persistence.sql.models.envelope import EnvelopeModel
    from shell.infrastructure.execution.persistence.sql.models.graph_execution import (
        GraphExecutionModel,
    )
    from shell.infrastructure.execution.persistence.sql.models.graph_execution_state_input import (
        GraphExecutionStateInputModel,
    )
    from shell.infrastructure.execution.persistence.sql.models.graph_execution_state_output import (
        GraphExecutionStateOutputModel,
    )
    from shell.infrastructure.execution.persistence.sql.models.graph_node_execution import (
        GraphNodeExecutionModel,
    )
    from shell.infrastructure.execution.persistence.sql.models.graph_node_execution_result import (
        GraphNodeExecutionResultModel,
    )
    from shell.infrastructure.execution.persistence.sql.models.graph_node_execution_state import (
        GraphNodeExecutionStateModel,
    )
    from shell.infrastructure.execution.persistence.sql.models.graph_node_transition_execution import (
        GraphNodeTransitionExecutionModel,
    )
    from shell.infrastructure.execution.persistence.sql.models.workflow import WorkflowModel

    WF_ID = f"{_DEV_ID_PREFIX}-workflow-1"
    existing = session.execute(
        select(WorkflowModel).where(WorkflowModel.id == WF_ID)
    ).scalar_one_or_none()
    if existing is not None:
        return

    task_id = f"{_DEV_ID_PREFIX}-task-simple-agent"
    graph_def_id = f"{_DEV_ID_PREFIX}-graph-simple-agent"
    ge_id = f"{_DEV_ID_PREFIX}-graph-execution-1"
    gne_id = f"{_DEV_ID_PREFIX}-gnode-execution-agent-1"

    # -- Workflow --
    wf = WorkflowModel(
        id=WF_ID,
        status="done",
        created_at=_NOW,
    )
    session.add(wf)

    # -- GraphExecution --
    ge = GraphExecutionModel(
        id=ge_id,
        task_execution_id=task_id,
        graph_definition_id=graph_def_id,
        status="COMPLETED",
        parent_graph_execution_id=None,
        state_input={"mode": "autonomous"},
        state_output={"result": "success"},
        depth=0,
        timeout_at=None,
        correlation_id="dev-correlation-1",
        tags={"env": "dev", "scenario": "sample"},
    )
    session.add(ge)

    # -- GraphExecutionStateInput --
    ges_input = GraphExecutionStateInputModel(
        id=f"{ge_id}-state-input-1",
        graph_execution_id=ge_id,
        payload={"context": "dev environment", "prompt": "Process sample scenario"},
        is_current=True,
        created_at=_NOW,
    )
    session.add(ges_input)

    # -- GraphExecutionStateOutput --
    ges_output = GraphExecutionStateOutputModel(
        id=f"{ge_id}-state-output-1",
        graph_execution_id=ge_id,
        payload={"status": "completed", "message": "Sample scenario completed"},
        is_current=True,
        created_at=_NOW,
    )
    session.add(ges_output)

    # -- GraphNodeExecution --
    gne = GraphNodeExecutionModel(
        id=gne_id,
        graph_execution_id=ge_id,
        position=0,
        mode="agent",
        role="agent",
        node_type="agent",
        model="gpt-4",
        command="",
        timeout=120,
        retries=1,
        log_level="INFO",
        max_step=10,
        no_ask_user=False,
        autopilot=True,
        task_execution_id=task_id,
        source_dir="/tmp/shell/dev/simple-agent",
        status_initial="idle",
        timeout_seconds=120,
        max_retries=1,
        retry_delay_seconds=5,
    )
    session.add(gne)

    # -- GraphNodeTransitionExecution --
    transition = GraphNodeTransitionExecutionModel(
        id=f"{_DEV_ID_PREFIX}-gtransition-exec-1",
        graph_execution_id=ge_id,
        source_node_execution_id=None,
        target_node_execution_id=gne_id,
        transition_type="sequence",
        priority=0,
        condition_expression=None,
        condition_language=None,
        join_wait_count=None,
        max_loop_count=0,
        timeout_seconds=None,
        retry_count=0,
        retry_delay_seconds=0,
        data_mapping=None,
        label="start -> agent",
        created_at=_NOW,
        updated_at=_NOW,
    )
    session.add(transition)

    # -- NodeState --
    ns = GraphNodeExecutionStateModel(
        id=f"{gne_id}-state-1",
        workflow_id=WF_ID,
        graph_node_execution_id=gne_id,
        status="done",
        step=1,
        updated_at=_NOW,
    )
    session.add(ns)

    # -- Envelope --
    env = EnvelopeModel(
        id=f"{_DEV_ID_PREFIX}-envelope-1",
        workflow_id=WF_ID,
        parent_id=None,
        correlation_id="dev-correlation-1",
        sender_graph_node_execution_id=gne_id,
        receiver_graph_node_execution_id=gne_id,
        source_role="agent",
        target_role="agent",
        sequence_id=1,
        step=1,
        status="delivered",
        stage="done",
        payload={"message": "Sample execution completed successfully"},
        artifact_uri="",
        archive_uri="",
        created_at=_NOW,
        updated_at=_NOW,
    )
    session.add(env)

    # -- NodeResult --
    result = GraphNodeExecutionResultModel(
        id=f"{gne_id}-result-1",
        graph_node_execution_id=gne_id,
        workflow_id=WF_ID,
        status="completed",
        stdout="[dev] Sample agent output:\nTask analyzed successfully.\nNo issues found.",
        stderr="",
        artifact_uri="file:///tmp/shell/dev/results/agent-1.json",
        created_at=_NOW,
    )
    session.add(result)


# ──────────────────────────────────────────────────────────────────────────────
# Scheduler
# ──────────────────────────────────────────────────────────────────────────────


def _seed_scheduler(session: Session) -> None:
    from shell.infrastructure.scheduling.persistence.sql.models.scheduler_definition import (
        SchedulerDefinitionModel,
    )
    from shell.infrastructure.scheduling.persistence.sql.models.scheduler_execution import (
        SchedulerExecutionModel,
    )

    sched_def_id = f"{_DEV_ID_PREFIX}-scheduler-outbox-relay"

    # -- SchedulerDefinition --
    definition = SchedulerDefinitionModel(
        id=sched_def_id,
        name="outbox-relay",
        description="Processes pending outbox events and publishes them to inbox",
        source_context="platform",
        trigger_event_type="OutboxPollingEvent",
        trigger_filter={"event_types": ["*"]},
        action_type="relay",
        action_config={
            "batch_size": 100,
            "max_retries": 3,
            "target": "outbox_to_inbox",
        },
        execution_policy={
            "max_concurrent": 1,
            "timeout_seconds": 60,
            "retry_policy": {"max_attempts": 3, "backoff_seconds": 5},
        },
        enabled=True,
        created_at=_NOW,
        updated_at=_NOW,
    )

    existing_def = session.execute(
        select(SchedulerDefinitionModel).where(SchedulerDefinitionModel.id == sched_def_id)
    ).scalar_one_or_none()
    if existing_def is None:
        session.add(definition)

    # -- SchedulerExecution --
    # Wrapped in try/except because the scheduler_execution table may be missing
    # the 'name' column if migrations are out of sync with the model definition.
    try:
        execution = SchedulerExecutionModel(
            id=f"{_DEV_ID_PREFIX}-scheduler-exec-outbox",
            scheduler_definition_id=sched_def_id,
            name="outbox-relay-executor",
            job_type="messaging",
            interval_seconds=10.0,
            batch_size=100,
            enabled=True,
            config={"poll_interval": 10, "batch_limit": 100},
            created_at=_NOW,
            updated_at=_NOW,
        )

        existing_exec = session.execute(
            select(SchedulerExecutionModel).where(SchedulerExecutionModel.id == execution.id)
        ).scalar_one_or_none()
        if existing_exec is None:
            session.add(execution)
    except Exception:
        pass  # Schema mismatch — non-critical for dev seed data
