"""Builders producing Definition BC ORM model instances for seeding and tests."""

from __future__ import annotations

from datetime import UTC, datetime

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
from shell.definition_service.infrastructure.definition.runner_config.persistence.sql.models.runner_config import (
    RunnerConfigModel,
)


def build_graph_definition_model(
    *,
    graph_definition_id: str,
    created_at: datetime | None = None,
) -> GraphDefinitionModel:
    """Build a GraphDefinitionModel with deterministic values."""
    return GraphDefinitionModel(
        id=graph_definition_id,
        created_at=created_at or datetime.now(tz=UTC),
    )


def build_node_definition_model(
    *,
    node_definition_id: str,
    node_type: str,
    max_step: int | None = None,
    created_at: datetime | None = None,
) -> NodeDefinitionModel:
    """Build a NodeDefinitionModel with deterministic values."""
    return NodeDefinitionModel(
        id=node_definition_id,
        node_type=node_type,
        max_step=max_step,
        created_at=created_at or datetime.now(tz=UTC),
    )


def build_node_link_definition_model(
    *,
    link_id: str,
    graph_definition_id: str,
    node_definition_id: str,
    created_at: datetime | None = None,
) -> NodeLinkDefinitionModel:
    """Build a NodeLinkDefinitionModel with deterministic values."""
    return NodeLinkDefinitionModel(
        id=link_id,
        graph_definition_id=graph_definition_id,
        node_definition_id=node_definition_id,
        created_at=created_at or datetime.now(tz=UTC),
    )


def build_graph_definition_embedding_model(
    *,
    embedding_id: str,
    graph_definition_id: str,
    text: str,
    embedding: bytes,
    embedding_model: str,
) -> GraphDefinitionEmbeddingModel:
    """Build a GraphDefinitionEmbeddingModel with deterministic values."""
    return GraphDefinitionEmbeddingModel(
        id=embedding_id,
        graph_definition_id=graph_definition_id,
        text=text,
        embedding=embedding,
        embedding_model=embedding_model,
    )


def build_runner_config_model(
    *,
    runner_config_id: str,
    package_name: str,
    kind: str,
    hash: str,
    body: dict[str, object],
    created_at: datetime | None = None,
) -> RunnerConfigModel:
    """Build a RunnerConfigModel with deterministic values."""
    return RunnerConfigModel(
        id=runner_config_id,
        package_name=package_name,
        kind=kind,
        hash=hash,
        body=body,
        created_at=created_at or datetime.now(tz=UTC),
    )


__all__ = [
    "build_graph_definition_embedding_model",
    "build_graph_definition_model",
    "build_node_definition_model",
    "build_node_link_definition_model",
    "build_runner_config_model",
]
