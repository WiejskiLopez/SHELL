"""Development seed data for the Definition bounded context.

Idempotent: records are inserted only when missing, so the seed can be
run repeatedly against the same database without creating duplicates.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from shell.definition_service.infrastructure.definition.graph_definition.persistence.sql.models.graph_definition import (
    GraphDefinitionModel,
)
from shell.definition_service.infrastructure.definition.runner_config.persistence.sql.models.runner_config import (
    RunnerConfigModel,
)
from shell.definition_service.infrastructure.definition.seed.builders import (
    build_graph_definition_embedding_model,
    build_graph_definition_model,
    build_node_definition_model,
    build_node_link_definition_model,
    build_runner_config_model,
)
from shell.platform.infrastructure.persistence.sql.seed_helpers import seed_if_missing

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

DEV_ID_PREFIX = "dev"

_RUNNER_CONFIGS_DATA: list[dict[str, Any]] = [
    {
        "runner_config_id": f"{DEV_ID_PREFIX}-runner-python",
        "package_name": "shell-runner-python",
        "kind": "python",
        "hash": "abc123def456",
        "body": {"entrypoint": "main.py", "interpreter": "python3.11"},
    },
    {
        "runner_config_id": f"{DEV_ID_PREFIX}-runner-shell",
        "package_name": "shell-runner-shell",
        "kind": "shell",
        "hash": "def789ghi012",
        "body": {"entrypoint": "run.sh", "shell": "bash"},
    },
    {
        "runner_config_id": f"{DEV_ID_PREFIX}-runner-node",
        "package_name": "shell-runner-node",
        "kind": "node",
        "hash": "jkl345mno678",
        "body": {"entrypoint": "index.js", "runtime": "node18"},
    },
]

_GRAPHS_DATA: list[tuple[str, list[dict[str, Any]]]] = [
    (
        f"{DEV_ID_PREFIX}-graph-simple-agent",
        [
            {
                "node_definition_id": f"{DEV_ID_PREFIX}-gnode-agent-1",
                "node_type": "agent",
                "max_step": 10,
            },
        ],
    ),
    (
        f"{DEV_ID_PREFIX}-graph-planner-worker",
        [
            {
                "node_definition_id": f"{DEV_ID_PREFIX}-gnode-planner-1",
                "node_type": "planner",
                "max_step": 15,
            },
            {
                "node_definition_id": f"{DEV_ID_PREFIX}-gnode-worker-1",
                "node_type": "worker",
                "max_step": 20,
            },
        ],
    ),
    (
        f"{DEV_ID_PREFIX}-graph-full-pipeline",
        [
            {
                "node_definition_id": f"{DEV_ID_PREFIX}-gnode-tasker-1",
                "node_type": "tasker",
                "max_step": 20,
            },
            {
                "node_definition_id": f"{DEV_ID_PREFIX}-gnode-router-1",
                "node_type": "router",
                "max_step": 10,
            },
            {
                "node_definition_id": f"{DEV_ID_PREFIX}-gnode-agent-2",
                "node_type": "agent",
                "max_step": 15,
            },
        ],
    ),
]


def seed_dev_sync(session: Session) -> None:
    """Insert dev runner configs and graph definitions when missing."""
    for config_data in _RUNNER_CONFIGS_DATA:
        seed_if_missing(
            session,
            RunnerConfigModel,
            str(config_data["runner_config_id"]),
            lambda config_data=config_data: build_runner_config_model(**config_data),
        )

    for graph_data in _GRAPHS_DATA:
        graph_id, node_data = graph_data
        existing_graph = session.execute(
            select(GraphDefinitionModel).where(GraphDefinitionModel.id == graph_id)
        ).scalar_one_or_none()
        if existing_graph is not None:
            continue

        session.add(build_graph_definition_model(graph_definition_id=graph_id))

        for node_index, node in enumerate(node_data):
            node_definition = build_node_definition_model(**node)
            session.add(node_definition)
            session.add(
                build_node_link_definition_model(
                    link_id=f"{graph_id}-link-{node_index}",
                    graph_definition_id=graph_id,
                    node_definition_id=node_definition.id,
                )
            )

        session.add(
            build_graph_definition_embedding_model(
                embedding_id=f"{graph_id}-embedding",
                graph_definition_id=graph_id,
                text=f"Embedding for {graph_id}",
                embedding=b"\x00\x01\x02",
                embedding_model="text-embedding-ada-002",
            )
        )


__all__ = ["DEV_ID_PREFIX", "seed_dev_sync"]
