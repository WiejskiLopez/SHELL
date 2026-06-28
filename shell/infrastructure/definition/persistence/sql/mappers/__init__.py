"""SQL ORM model <-> domain entity mappers for Definition BC."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.definition.aggregates.rag_document import RagChunk, RagDocument
from shell.domain.definition.aggregates.graph_definition.graph_definition import GraphDefinition
from shell.domain.definition.aggregates.graph_node_definition.graph_node_definition import (
    GraphNodeDefinition,
)
from shell.domain.definition.aggregates.graph_node_transition_definition.value_objects.graph_node_transition_definition_id import (
    GraphNodeTransitionDefinitionId,
)
from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
    GraphDefinitionId,
)
from shell.domain.definition.aggregates.graph_node_definition.value_objects.graph_node_definition_id import (
    GraphNodeDefinitionId,
)
from shell.domain.definition.entities.runner_config import RunnerConfig
from shell.domain.definition.value_objects.ids import (
    RagChunkId,
    RagDocumentId,
    RunnerConfigId,
)
from shell.domain.platform.value_objects.hash import Hash
from shell.domain.platform.value_objects.mode import Mode
from shell.infrastructure.definition.persistence.sql.models import (
    GraphDefinitionModel,
    GraphNodeDefinitionModel,
    GraphNodeTransitionDefinitionModel,
    RagChunkModel,
    RagDocumentModel,
    RunnerConfigModel,
)


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


# ---------------------------------------------------------------------------
# RunnerConfig
# ---------------------------------------------------------------------------


def runner_config_model_to_entity(runner_config_model: RunnerConfigModel) -> RunnerConfig:
    return RunnerConfig(
        id=RunnerConfigId(runner_config_model.id),
        package_name=runner_config_model.package_name,
        kind=runner_config_model.kind,
        hash=Hash(runner_config_model.hash),
        body=dict(runner_config_model.body),
        created_at=_ensure_utc(runner_config_model.created_at),
    )


def runner_config_entity_to_model(runner_config: RunnerConfig) -> RunnerConfigModel:
    return RunnerConfigModel(
        id=runner_config.id.value,
        package_name=runner_config.package_name,
        kind=runner_config.kind,
        hash=runner_config.hash.value,
        body=runner_config.body,
        created_at=runner_config.created_at,
    )


def runner_config_update_model(model: RunnerConfigModel, entity: RunnerConfig) -> None:
    model.package_name = entity.package_name
    model.kind = entity.kind
    model.hash = entity.hash.value if hasattr(entity.hash, 'value') else entity.hash
    model.body = entity.body
    model.created_at = entity.created_at


# ---------------------------------------------------------------------------
# GraphDefinition
# ---------------------------------------------------------------------------


def graph_definition_model_to_entity(
    graph_definition_model: GraphDefinitionModel,
) -> GraphDefinition:
    return GraphDefinition(
        id=GraphDefinitionId(graph_definition_model.id),
        name=graph_definition_model.name,
        purpose=graph_definition_model.purpose,
        system_role=graph_definition_model.system_role,
        graph_node_definition_ids=[
            GraphNodeDefinitionId(node.id)
            for node in (graph_definition_model.graph_node_execution_models or [])
        ],
        transition_definition_ids=[
            GraphNodeTransitionDefinitionId(t.id)
            for t in (graph_definition_model.graph_node_transition_definition_models or [])
        ],
    )


def graph_definition_entity_to_model(
    graph_definition: GraphDefinition,
) -> GraphDefinitionModel:
    graph_definition_model = GraphDefinitionModel(
        id=str(graph_definition.id.value),
        name=str(graph_definition.name.value),
        purpose=str(graph_definition.purpose.value),
        system_role=str(graph_definition.system_role.value) if graph_definition.system_role is not None else None,
    )
    return graph_definition_model


def graph_definition_update_model(model: GraphDefinitionModel, entity: GraphDefinition) -> None:
    model.name = str(entity.name.value)
    model.purpose = str(entity.purpose.value)
    model.system_role = str(entity.system_role.value) if entity.system_role is not None else None


def graph_node_definition_model_to_entity(
    graph_node_definition_model: GraphNodeDefinitionModel,
) -> GraphNodeDefinition:
    return GraphNodeDefinition(
        id=GraphNodeDefinitionId(graph_node_definition_model.id),
        position=graph_node_definition_model.position,
        mode=Mode(graph_node_definition_model.mode),
        role=graph_node_definition_model.role,
        node_type=graph_node_definition_model.node_type,
        model=graph_node_definition_model.model or "",
        command=graph_node_definition_model.command,
        timeout=graph_node_definition_model.timeout,
        retries=graph_node_definition_model.retries,
        log_level=graph_node_definition_model.log_level,
        max_step=graph_node_definition_model.max_step,
        no_ask_user=bool(graph_node_definition_model.no_ask_user),
        autopilot=bool(graph_node_definition_model.autopilot),
        status_initial=graph_node_definition_model.status_initial,
        script=graph_node_definition_model.script or "",
        script_type=graph_node_definition_model.script_type or "",
    )


def graph_node_definition_entity_to_model(
    graph_node_definition: GraphNodeDefinition,
    graph_definition_id: str,
) -> GraphNodeDefinitionModel:
    return GraphNodeDefinitionModel(
        id=graph_node_definition.id.value,
        graph_definition_id=graph_definition_id,
        position=graph_node_definition.position,
        mode=graph_node_definition.mode.value,
        role=graph_node_definition.role,
        node_type=graph_node_definition.node_type,
        model=graph_node_definition.model,
        command=graph_node_definition.command,
        timeout=graph_node_definition.timeout,
        retries=graph_node_definition.retries,
        log_level=graph_node_definition.log_level,
        max_step=graph_node_definition.max_step,
        no_ask_user=graph_node_definition.no_ask_user,
        autopilot=graph_node_definition.autopilot,
        status_initial=graph_node_definition.status_initial,
        script=graph_node_definition.script,
        script_type=graph_node_definition.script_type,
    )


def graph_node_definition_update_model(model: GraphNodeDefinitionModel, entity: GraphNodeDefinition) -> None:
    model.position = entity.position
    model.mode = entity.mode.value if hasattr(entity.mode, 'value') else entity.mode
    model.role = entity.role
    model.node_type = entity.node_type
    model.model = entity.model or ""
    model.command = entity.command
    model.timeout = entity.timeout
    model.retries = entity.retries
    model.log_level = entity.log_level
    model.max_step = entity.max_step
    model.no_ask_user = bool(entity.no_ask_user) if entity.no_ask_user is not None else False
    model.autopilot = bool(entity.autopilot) if entity.autopilot is not None else False
    model.status_initial = entity.status_initial
    model.script = entity.script or ""
    model.script_type = entity.script_type or ""


# ---------------------------------------------------------------------------
# RagDocument
# ---------------------------------------------------------------------------


def rag_document_model_to_entity(rag_document_model: RagDocumentModel) -> RagDocument:
    return RagDocument(
        id=RagDocumentId(rag_document_model.id),
        source_uri=rag_document_model.source_uri,
        title=rag_document_model.title,
        domain=rag_document_model.domain,
        created_at=_ensure_utc(rag_document_model.created_at),
        chunks=[
            rag_chunk_model_to_entity(c)
            for c in sorted(rag_document_model.chunks, key=lambda c: c.chunk_index)
        ],
    )


def rag_document_entity_to_model(rag_document: RagDocument) -> RagDocumentModel:
    model = RagDocumentModel(
        id=rag_document.id.value,
        source_uri=rag_document.source_uri.value if hasattr(rag_document.source_uri, 'value') else rag_document.source_uri,
        title=rag_document.title.value if hasattr(rag_document.title, 'value') else rag_document.title,
        domain=rag_document.domain.value if hasattr(rag_document.domain, 'value') else rag_document.domain,
        created_at=rag_document.created_at.value if hasattr(rag_document.created_at, 'value') else rag_document.created_at,
    )
    model.chunks = [rag_chunk_entity_to_model(c) for c in rag_document.chunks]
    return model


def rag_document_update_model(model: RagDocumentModel, entity: RagDocument) -> None:
    model.source_uri = entity.source_uri.value if hasattr(entity.source_uri, 'value') else entity.source_uri
    model.title = entity.title.value if hasattr(entity.title, 'value') else entity.title
    model.domain = entity.domain.value if hasattr(entity.domain, 'value') else entity.domain
    model.created_at = entity.created_at.value if hasattr(entity.created_at, 'value') else entity.created_at
    # Chunks are managed separately


# ---------------------------------------------------------------------------
# RagChunk
# ---------------------------------------------------------------------------


def rag_chunk_model_to_entity(rag_chunk_model: RagChunkModel) -> RagChunk:
    from shell.domain.definition.value_objects.chunk_index import ChunkIndex
    from shell.domain.definition.value_objects.chunk_text import ChunkText
    from shell.domain.definition.value_objects.embedding import Embedding
    from shell.domain.definition.value_objects.embedding_model import EmbeddingModel

    return RagChunk(
        id=RagChunkId(rag_chunk_model.id),
        document_id=RagDocumentId(rag_chunk_model.document_id),
        chunk_index=ChunkIndex(rag_chunk_model.chunk_index),
        chunk_text=ChunkText(rag_chunk_model.chunk_text),
        embedding=Embedding(rag_chunk_model.embedding),
        embedding_model=EmbeddingModel(rag_chunk_model.embedding_model),
    )


def rag_chunk_entity_to_model(rag_chunk: RagChunk) -> RagChunkModel:
    return RagChunkModel(
        id=rag_chunk.id.value,
        document_id=rag_chunk.document_id.value,
        chunk_index=rag_chunk.chunk_index.value,
        chunk_text=rag_chunk.chunk_text.value,
        embedding=rag_chunk.embedding.value,
        embedding_model=rag_chunk.embedding_model.value,
    )
