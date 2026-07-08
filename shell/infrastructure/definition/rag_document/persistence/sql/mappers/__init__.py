from shell.domain.definition.aggregates.rag_document import RagChunk, RagDocument
from shell.domain.definition.value_objects.chunk_index import ChunkIndex
from shell.domain.definition.value_objects.chunk_text import ChunkText
from shell.domain.definition.value_objects.domain_tag import DomainTag
from shell.domain.definition.value_objects.embedding import Embedding
from shell.domain.definition.value_objects.embedding_model import EmbeddingModel
from shell.domain.definition.value_objects.ids import RagChunkId, RagDocumentId
from shell.domain.definition.value_objects.source_uri import SourceUri
from shell.domain.definition.value_objects.title import Title
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.infrastructure.definition.rag_document.persistence.sql.models import (
    RagChunkModel,
    RagDocumentModel,
)


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
