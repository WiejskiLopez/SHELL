"""Builders producing Execution BC ORM model instances for seeding and tests."""

from __future__ import annotations

from datetime import UTC, datetime

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
from shell.execution_service.infrastructure.execution.task_execution.persistence.sql.models.task_execution import (
    TaskExecutionModel,
)
from shell.execution_service.infrastructure.execution.task_execution_state.persistence.sql.models.task_execution_state import (
    TaskExecutionStateModel,
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


def build_task_execution_model(
    *,
    task_execution_id: str,
    status: str,
    name: str,
    work_dir: str,
    workflow_id: str,
    created_at: datetime | None = None,
) -> TaskExecutionModel:
    """Build a TaskExecutionModel with deterministic values."""
    return TaskExecutionModel(
        id=task_execution_id,
        status=status,
        name=name,
        work_dir=work_dir,
        workflow_id=workflow_id,
        created_at=created_at or datetime.now(tz=UTC),
    )


def build_task_execution_state_model(
    *,
    state_id: str,
    task_execution_id: str,
    direction: str,
    state_data: dict[str, object],
    created_at: datetime | None = None,
) -> TaskExecutionStateModel:
    """Build a TaskExecutionStateModel with deterministic values."""
    return TaskExecutionStateModel(
        id=state_id,
        task_execution_id=task_execution_id,
        direction=direction,
        state_data=state_data,
        created_at=created_at or datetime.now(tz=UTC),
    )


def build_workflow_model(
    *,
    workflow_id: str,
    status: str,
    session_id: str,
    project_id: str,
    created_at: datetime | None = None,
) -> WorkflowModel:
    """Build a WorkflowModel with deterministic values."""
    return WorkflowModel(
        id=workflow_id,
        status=status,
        session_id=session_id,
        project_id=project_id,
        created_at=created_at or datetime.now(tz=UTC),
    )


def build_user_execution_model(
    *,
    user_execution_id: str,
    user_id: str,
    created_at: datetime | None = None,
) -> UserExecutionModel:
    """Build a UserExecutionModel with deterministic values."""
    return UserExecutionModel(
        id=user_execution_id,
        user_id=user_id,
        created_at=created_at or datetime.now(tz=UTC),
    )


def build_user_execution_state_model(
    *,
    state_id: str,
    user_execution_id: str,
    direction: str,
    state_data: dict[str, object],
    created_at: datetime | None = None,
) -> UserExecutionStateModel:
    """Build a UserExecutionStateModel with deterministic values."""
    return UserExecutionStateModel(
        id=state_id,
        user_execution_id=user_execution_id,
        direction=direction,
        state_data=state_data,
        created_at=created_at or datetime.now(tz=UTC),
    )


def build_session_execution_model(
    *,
    session_execution_id: str,
    user_execution_id: str,
    session_id: str,
    created_at: datetime | None = None,
) -> SessionExecutionModel:
    """Build a SessionExecutionModel with deterministic values."""
    return SessionExecutionModel(
        id=session_execution_id,
        user_execution_id=user_execution_id,
        session_id=session_id,
        created_at=created_at or datetime.now(tz=UTC),
    )


def build_session_execution_state_model(
    *,
    state_id: str,
    session_execution_id: str,
    direction: str,
    state_data: dict[str, object],
    created_at: datetime | None = None,
) -> SessionExecutionStateModel:
    """Build a SessionExecutionStateModel with deterministic values."""
    return SessionExecutionStateModel(
        id=state_id,
        session_execution_id=session_execution_id,
        direction=direction,
        state_data=state_data,
        created_at=created_at or datetime.now(tz=UTC),
    )


def build_graph_execution_model(
    *,
    graph_execution_id: str,
    task_execution_id: str,
    graph_definition_id: str,
    status: str,
    parent_graph_execution_id: str | None,
    state_input: dict[str, object],
    state_output: dict[str, object],
    depth: int,
    timeout_at: datetime | None,
    correlation_id: str,
    tags: dict[str, object],
    created_at: datetime | None = None,
) -> GraphExecutionModel:
    """Build a GraphExecutionModel with deterministic values."""
    return GraphExecutionModel(
        id=graph_execution_id,
        task_execution_id=task_execution_id,
        graph_definition_id=graph_definition_id,
        status=status,
        parent_graph_execution_id=parent_graph_execution_id,
        state_input=state_input,
        state_output=state_output,
        depth=depth,
        timeout_at=timeout_at,
        correlation_id=correlation_id,
        tags=tags,
        created_at=created_at or datetime.now(tz=UTC),
    )


def build_graph_execution_state_model(
    *,
    state_id: str,
    graph_execution_id: str,
    direction: str,
    state_data: dict[str, object],
    created_at: datetime | None = None,
) -> GraphExecutionStateModel:
    """Build a GraphExecutionStateModel with deterministic values."""
    return GraphExecutionStateModel(
        id=state_id,
        graph_execution_id=graph_execution_id,
        direction=direction,
        state_data=state_data,
        created_at=created_at or datetime.now(tz=UTC),
    )


def build_node_execution_model(
    *,
    node_execution_id: str,
    position: int,
    node_type: str,
    model: str,
    command: str,
    retries: int,
    log_level: str,
    max_step: int,
    no_ask_user: bool,
    autopilot: bool,
    task_execution_id: str,
    source_dir: str,
    status: str,
    status_initial: str,
    created_at: datetime | None = None,
) -> NodeExecutionModel:
    """Build a NodeExecutionModel with deterministic values."""
    return NodeExecutionModel(
        id=node_execution_id,
        position=position,
        node_type=node_type,
        model=model,
        command=command,
        retries=retries,
        log_level=log_level,
        max_step=max_step,
        no_ask_user=no_ask_user,
        autopilot=autopilot,
        task_execution_id=task_execution_id,
        source_dir=source_dir,
        status=status,
        status_initial=status_initial,
        created_at=created_at or datetime.now(tz=UTC),
    )


def build_node_execution_state_model(
    *,
    state_id: str,
    node_execution_id: str,
    direction: str,
    state_data: dict[str, object],
    created_at: datetime | None = None,
) -> NodeExecutionStateModel:
    """Build a NodeExecutionStateModel with deterministic values."""
    return NodeExecutionStateModel(
        id=state_id,
        node_execution_id=node_execution_id,
        direction=direction,
        state_data=state_data,
        created_at=created_at or datetime.now(tz=UTC),
    )


def build_node_execution_result_model(
    *,
    result_id: str,
    node_execution_id: str,
    workflow_id: str,
    status: str,
    stdout: str,
    stderr: str,
    artifact_uri: str,
    created_at: datetime | None = None,
) -> NodeExecutionResultModel:
    """Build a NodeExecutionResultModel with deterministic values."""
    return NodeExecutionResultModel(
        id=result_id,
        node_execution_id=node_execution_id,
        workflow_id=workflow_id,
        status=status,
        stdout=stdout,
        stderr=stderr,
        artifact_uri=artifact_uri,
        created_at=created_at or datetime.now(tz=UTC),
    )


def build_node_link_execution_model(
    *,
    link_id: str,
    graph_execution_id: str,
    node_execution_id: str,
) -> NodeLinkExecutionModel:
    """Build a NodeLinkExecutionModel with deterministic values."""
    return NodeLinkExecutionModel(
        id=link_id,
        graph_execution_id=graph_execution_id,
        node_execution_id=node_execution_id,
    )


def build_agent_execution_model(
    *,
    agent_execution_id: str,
    node_execution_id: str,
    created_at: datetime | None = None,
) -> AgentExecutionModel:
    """Build an AgentExecutionModel with deterministic values."""
    now = created_at or datetime.now(tz=UTC)
    return AgentExecutionModel(
        id=agent_execution_id,
        node_execution_id=node_execution_id,
        created_at=now,
        changed_at=now,
    )


def build_agent_config_execution_model(
    *,
    config_id: str,
    agent_execution_id: str,
    config_data: str,
    created_at: datetime | None = None,
) -> AgentConfigExecutionModel:
    """Build an AgentConfigExecutionModel with deterministic values."""
    return AgentConfigExecutionModel(
        id=config_id,
        agent_execution_id=agent_execution_id,
        config_data=config_data,
        created_at=created_at or datetime.now(tz=UTC),
    )


def build_agent_skill_execution_model(
    *,
    skill_id: str,
    agent_execution_id: str,
    skill_data: dict[str, object],
    created_at: datetime | None = None,
) -> AgentSkillExecutionModel:
    """Build an AgentSkillExecutionModel with deterministic values."""
    return AgentSkillExecutionModel(
        id=skill_id,
        agent_execution_id=agent_execution_id,
        skill_data=skill_data,
        created_at=created_at or datetime.now(tz=UTC),
    )


def build_edge_execution_model(
    *,
    edge_execution_id: str,
    edge_definition_id: str,
    source_node_execution_id: str,
    target_node_execution_id: str | None,
    created_at: datetime | None = None,
) -> EdgeExecutionModel:
    """Build an EdgeExecutionModel with deterministic values."""
    now = created_at or datetime.now(tz=UTC)
    return EdgeExecutionModel(
        id=edge_execution_id,
        edge_definition_id=edge_definition_id,
        source_node_execution_id=source_node_execution_id,
        target_node_execution_id=target_node_execution_id,
        created_at=now,
        changed_at=now,
    )


def build_edge_link_execution_model(
    *,
    link_id: str,
    node_execution_id: str,
    edge_execution_id: str,
    created_at: datetime | None = None,
) -> EdgeLinkExecutionModel:
    """Build an EdgeLinkExecutionModel with deterministic values."""
    now = created_at or datetime.now(tz=UTC)
    return EdgeLinkExecutionModel(
        id=link_id,
        node_execution_id=node_execution_id,
        edge_execution_id=edge_execution_id,
        created_at=now,
        changed_at=now,
    )


__all__ = [
    "build_agent_config_execution_model",
    "build_agent_execution_model",
    "build_agent_skill_execution_model",
    "build_edge_execution_model",
    "build_edge_link_execution_model",
    "build_graph_execution_model",
    "build_graph_execution_state_model",
    "build_node_execution_model",
    "build_node_execution_result_model",
    "build_node_execution_state_model",
    "build_node_link_execution_model",
    "build_session_execution_model",
    "build_session_execution_state_model",
    "build_task_execution_model",
    "build_task_execution_state_model",
    "build_user_execution_model",
    "build_user_execution_state_model",
    "build_workflow_model",
]
