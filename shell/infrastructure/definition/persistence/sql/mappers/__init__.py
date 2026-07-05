"""SQL ORM model <-> domain entity mappers for Definition BC."""

from __future__ import annotations

from shell.domain.definition.aggregates.graph_definition.graph_definition import GraphDefinition
from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
    GraphDefinitionId,
)
from shell.domain.definition.aggregates.node_definition.node_definition import (
    NodeDefinition,
)
from shell.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
    NodeDefinitionId as _AggNodeDefinitionId,
)
from shell.domain.definition.aggregates.rag_document import RagChunk, RagDocument
from shell.domain.definition.entities.runner_config import RunnerConfig
from shell.domain.definition.value_objects.autopilot import Autopilot
from shell.domain.definition.value_objects.chunk_index import ChunkIndex
from shell.domain.definition.value_objects.chunk_text import ChunkText
from shell.domain.definition.value_objects.command_text import CommandText
from shell.domain.definition.value_objects.domain_tag import DomainTag
from shell.domain.definition.value_objects.embedding import Embedding
from shell.domain.definition.value_objects.embedding_model import EmbeddingModel
from shell.domain.definition.value_objects.graph_name import GraphName
from shell.domain.definition.value_objects.ids import (
    NodeTransitionDefinitionId,
    RagChunkId,
    RagDocumentId,
    RunnerConfigId,
)
from shell.domain.definition.value_objects.initial_status import InitialStatus
from shell.domain.definition.value_objects.log_level import LogLevel
from shell.domain.definition.value_objects.max_step import MaxStep
from shell.domain.definition.value_objects.model_name import ModelName
from shell.domain.definition.value_objects.no_ask_user import NoAskUser
from shell.domain.definition.value_objects.node_position import NodePosition
from shell.domain.definition.value_objects.node_role_name import NodeRoleName
from shell.domain.definition.value_objects.node_type_name import NodeTypeName
from shell.domain.definition.value_objects.package_name import PackageName
from shell.domain.definition.value_objects.purpose import Purpose
from shell.domain.definition.value_objects.retry_count import RetryCount
from shell.domain.definition.value_objects.runner_body import RunnerBody
from shell.domain.definition.value_objects.runner_kind import RunnerKind
from shell.domain.definition.value_objects.script_text import ScriptText
from shell.domain.definition.value_objects.script_type_name import ScriptTypeName
from shell.domain.definition.value_objects.source_uri import SourceUri
from shell.domain.definition.value_objects.system_role import SystemRole
from shell.domain.definition.value_objects.title import Title
from shell.domain.definition.value_objects.transition_timeout_seconds import (
    TransitionTimeoutSeconds,
)
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.hash import Hash
from shell.domain.platform.value_objects.mode import Mode
from shell.infrastructure.definition.persistence.sql.models import (
    GraphDefinitionModel,
    NodeDefinitionModel,
    RagChunkModel,
    RagDocumentModel,
    RunnerConfigModel,
)

# ---------------------------------------------------------------------------
# RunnerConfig
# ---------------------------------------------------------------------------


def runner_config_model_to_entity(runner_config_model: RunnerConfigModel) -> RunnerConfig:
    return RunnerConfig(
        id=RunnerConfigId(runner_config_model.id),
        package_name=PackageName(runner_config_model.package_name),
        kind=RunnerKind(runner_config_model.kind),
        hash=Hash(runner_config_model.hash),
        body=RunnerBody(dict(runner_config_model.body)),
        created_at=CreatedAt.from_datetime(runner_config_model.created_at),
    )


def runner_config_entity_to_model(runner_config: RunnerConfig) -> RunnerConfigModel:
    return RunnerConfigModel(
        id=runner_config.id.value,
        package_name=str(runner_config.package_name),
        kind=str(runner_config.kind),
        hash=runner_config.hash.value,
        body=runner_config.body.value,
        created_at=runner_config.created_at.value,
    )


def runner_config_update_model(model: RunnerConfigModel, entity: RunnerConfig) -> None:
    model.package_name = str(entity.package_name)
    model.kind = str(entity.kind)
    model.hash = entity.hash.value
    model.body = entity.body.value
    model.created_at = entity.created_at.value


# ---------------------------------------------------------------------------
# GraphDefinition
# ---------------------------------------------------------------------------


def graph_definition_model_to_entity(
    graph_definition_model: GraphDefinitionModel,
) -> GraphDefinition:
    return GraphDefinition(
        id=GraphDefinitionId(graph_definition_model.id),
        name=GraphName(graph_definition_model.name),
        purpose=Purpose(graph_definition_model.purpose),
        system_role=SystemRole(graph_definition_model.system_role)
        if graph_definition_model.system_role is not None
        else None,
        transition_definition_ids=[
            NodeTransitionDefinitionId(t.id)
            for t in (graph_definition_model.node_transition_definition_models or [])
        ],
    )


def graph_definition_entity_to_model(
    graph_definition: GraphDefinition,
) -> GraphDefinitionModel:
    graph_definition_model = GraphDefinitionModel(
        id=str(graph_definition.id.value),
        name=str(graph_definition.name.value),
        purpose=str(graph_definition.purpose.value),
        system_role=str(graph_definition.system_role.value)
        if graph_definition.system_role is not None
        else None,
    )
    return graph_definition_model


def graph_definition_update_model(model: GraphDefinitionModel, entity: GraphDefinition) -> None:
    model.name = str(entity.name.value)
    model.purpose = str(entity.purpose.value)
    model.system_role = str(entity.system_role.value) if entity.system_role is not None else None


def node_definition_model_to_entity(
    node_definition_model: NodeDefinitionModel,
) -> NodeDefinition:
    return NodeDefinition(
        id=_AggNodeDefinitionId(node_definition_model.id),
        position=NodePosition(node_definition_model.position),
        mode=Mode(str(node_definition_model.mode)),
        role=NodeRoleName(node_definition_model.role),
        node_type=NodeTypeName(node_definition_model.node_type),
        model=ModelName(node_definition_model.model)
        if node_definition_model.model is not None
        else None,
        command=CommandText(node_definition_model.command),
        timeout=TransitionTimeoutSeconds(node_definition_model.timeout),
        retries=RetryCount(node_definition_model.retries),
        log_level=LogLevel(node_definition_model.log_level),
        max_step=MaxStep(node_definition_model.max_step)
        if node_definition_model.max_step is not None
        else None,
        no_ask_user=NoAskUser(bool(node_definition_model.no_ask_user))
        if node_definition_model.no_ask_user is not None
        else None,
        autopilot=Autopilot(bool(node_definition_model.autopilot))
        if node_definition_model.autopilot is not None
        else None,
        status_initial=InitialStatus(node_definition_model.status_initial),
        script=ScriptText(node_definition_model.script)
        if node_definition_model.script is not None
        else None,
        script_type=ScriptTypeName(node_definition_model.script_type)
        if node_definition_model.script_type is not None
        else None,
    )


def node_definition_entity_to_model(
    node_definition: NodeDefinition,
) -> NodeDefinitionModel:
    return NodeDefinitionModel(
        id=node_definition.id.value,
        position=node_definition.position.value,
        mode=node_definition.mode.value,
        role=node_definition.role.value,
        node_type=node_definition.node_type.value,
        model=node_definition.model.value
        if node_definition.model is not None
        else None,
        command=node_definition.command.value
        if node_definition.command is not None
        else "",
        timeout=node_definition.timeout.value
        if node_definition.timeout is not None
        else 0,
        retries=node_definition.retries.value
        if node_definition.retries is not None
        else 0,
        log_level=node_definition.log_level.value
        if node_definition.log_level is not None
        else "",
        max_step=node_definition.max_step.value
        if node_definition.max_step is not None
        else None,
        no_ask_user=node_definition.no_ask_user.value
        if node_definition.no_ask_user is not None
        else None,
        autopilot=node_definition.autopilot.value
        if node_definition.autopilot is not None
        else None,
        status_initial=node_definition.status_initial.value
        if node_definition.status_initial is not None
        else "",
        script=node_definition.script.value
        if node_definition.script is not None
        else None,
        script_type=node_definition.script_type.value
        if node_definition.script_type is not None
        else None,
    )


def node_definition_update_model(
    model: NodeDefinitionModel, entity: NodeDefinition
) -> None:
    model.position = entity.position.value
    model.mode = entity.mode.value
    model.role = entity.role.value
    model.node_type = entity.node_type.value
    model.model = entity.model.value if entity.model is not None else None
    model.command = entity.command.value if entity.command is not None else ""
    model.timeout = (
        entity.timeout.value
        if entity.timeout is not None and entity.timeout.value is not None
        else 0
    )
    model.retries = entity.retries.value if entity.retries is not None else 0
    model.log_level = entity.log_level.value if entity.log_level is not None else ""
    model.max_step = entity.max_step.value if entity.max_step is not None else None
    model.no_ask_user = entity.no_ask_user.value if entity.no_ask_user is not None else None
    model.autopilot = entity.autopilot.value if entity.autopilot is not None else None
    model.status_initial = entity.status_initial.value if entity.status_initial is not None else ""
    model.script = entity.script.value if entity.script is not None else None
    model.script_type = entity.script_type.value if entity.script_type is not None else None


# ---------------------------------------------------------------------------
# RagDocument
# ---------------------------------------------------------------------------


def rag_document_model_to_entity(rag_document_model: RagDocumentModel) -> RagDocument:
    return RagDocument(
        id=RagDocumentId(rag_document_model.id),
        source_uri=SourceUri(rag_document_model.source_uri),
        title=Title(rag_document_model.title),
        domain=DomainTag(rag_document_model.domain),
        created_at=CreatedAt.from_datetime(rag_document_model.created_at),
        chunks=[
            rag_chunk_model_to_entity(c)
            for c in sorted(rag_document_model.chunks, key=lambda c: c.chunk_index)
        ],
    )


def rag_document_entity_to_model(rag_document: RagDocument) -> RagDocumentModel:
    model = RagDocumentModel(
        id=rag_document.id.value,
        source_uri=str(rag_document.source_uri),
        title=str(rag_document.title),
        domain=str(rag_document.domain),
        created_at=rag_document.created_at.value,
    )
    model.chunks = [rag_chunk_entity_to_model(c) for c in rag_document.chunks]
    return model


def rag_document_update_model(model: RagDocumentModel, entity: RagDocument) -> None:
    model.source_uri = str(entity.source_uri)
    model.title = str(entity.title)
    model.domain = str(entity.domain)
    model.created_at = entity.created_at.value
    # Chunks are managed separately


# ---------------------------------------------------------------------------
# RagChunk
# ---------------------------------------------------------------------------


def rag_chunk_model_to_entity(rag_chunk_model: RagChunkModel) -> RagChunk:
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
