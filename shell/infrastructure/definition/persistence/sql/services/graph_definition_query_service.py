from __future__ import annotations

import logging
import math
import struct
from typing import TYPE_CHECKING

from shell.application.definition.dto.graph_definition import GraphDefinitionDto
from shell.application.definition.dto.graph_node_definition import GraphNodeDefinitionDto
from shell.infrastructure.definition.persistence.sql.models import (
    GraphDefinitionModel,
)
from shell.infrastructure.definition.persistence.sql.models.graph_definition_embedding import (
    GraphDefinitionEmbeddingModel,
)
from sqlalchemy import select
from sqlalchemy.orm import joinedload

if TYPE_CHECKING:
    from shell.domain.definition.services.rag_index_service import Embedder
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)


class SqlGraphDefinitionQueryService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        embedder: Embedder,
    ) -> None:
        self._session_factory = session_factory
        self._embedder = embedder

    async def get_graph_definition_by_semantic_name(
        self, payload: dict[str, object],
    ) -> GraphDefinitionDto | None:
        default_role = payload.get("default_graph_definition")
        if default_role:
            dto = await self.get_graph_definition_by_system_role(str(default_role))
            if dto is not None:
                return dto

        query_text = str(payload.get("query", ""))
        if not query_text:
            return None

        vector = self._embedder.embed_text(query_text)
        vector_bytes = struct.pack(f"{len(vector)}f", *vector)

        async with self._session_factory() as session:
            embedding = await self._find_nearest(session, vector_bytes)
            if embedding is None:
                return None

            stmt = (
                select(GraphDefinitionModel)
                .options(joinedload(GraphDefinitionModel.graph_node_execution_models))
                .where(GraphDefinitionModel.id == embedding.graph_definition_id)
            )
            res = await session.execute(stmt)
            model = res.unique().scalar_one_or_none()
            if model is None:
                return None
            return self._to_dto(model)

    async def _find_nearest(
        self,
        session: AsyncSession,
        query_embedding: bytes,
    ) -> GraphDefinitionEmbeddingModel | None:
        try:
            return await self._pgvector_search(session, query_embedding)
        except Exception:
            logger.info("pgvector not available, falling back to in-memory search")
            return await self._in_memory_search(session, query_embedding)

    async def _pgvector_search(
        self,
        session: AsyncSession,
        query_embedding: bytes,
    ) -> GraphDefinitionEmbeddingModel | None:
        from sqlalchemy import text

        dim = len(query_embedding) // 4
        query_vec = list(struct.unpack(f"{dim}f", query_embedding))
        vector_literal = "[" + ",".join(str(v) for v in query_vec) + "]"
        stmt = text(
            """
            SELECT gde.id, gde.graph_definition_id, gde.text,
                   gde.embedding, gde.embedding_model
            FROM graph_definition_embedding gde
            ORDER BY gde.embedding <=> :query_vec::vector
            LIMIT 1
            """
        )
        row = (await session.execute(stmt, {"query_vec": vector_literal})).mappings().first()
        if row is None:
            return None
        return GraphDefinitionEmbeddingModel(
            id=row["id"],
            graph_definition_id=row["graph_definition_id"],
            text=row["text"],
            embedding=row["embedding"],
            embedding_model=row["embedding_model"],
        )

    async def _in_memory_search(
        self,
        session: AsyncSession,
        query_embedding: bytes,
    ) -> GraphDefinitionEmbeddingModel | None:
        stmt = select(GraphDefinitionEmbeddingModel)
        rows = (await session.execute(stmt)).scalars().all()
        if not rows:
            return None

        dim = len(query_embedding) // 4
        query_vec = list(struct.unpack(f"{dim}f", query_embedding))
        best_score = -1.0
        best_model: GraphDefinitionEmbeddingModel | None = None

        for model in rows:
            chunk_vec = list(
                struct.unpack(f"{len(model.embedding) // 4}f", model.embedding)
            )
            score = self._cosine_similarity(query_vec, chunk_vec)
            if score > best_score:
                best_score = score
                best_model = model

        return best_model

    @staticmethod
    def _cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
        if len(vector_a) != len(vector_b) or not vector_a:
            return 0.0
        dot = sum(a * b for a, b in zip(vector_a, vector_b, strict=False))
        norm_a = math.sqrt(sum(a * a for a in vector_a))
        norm_b = math.sqrt(sum(b * b for b in vector_b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    async def get_graph_definition(self, definition_id: str) -> GraphDefinitionDto | None:
        async with self._session_factory() as session:
            stmt = (
                select(GraphDefinitionModel)
                .options(joinedload(GraphDefinitionModel.graph_node_execution_models))
                .where(GraphDefinitionModel.id == definition_id)
            )
            res = await session.execute(stmt)
            model = res.unique().scalar_one_or_none()
            if model is None:
                return None
            return self._to_dto(model)

    async def get_graph_definition_by_system_role(
        self, role: str,
    ) -> GraphDefinitionDto | None:
        async with self._session_factory() as session:
            stmt = (
                select(GraphDefinitionModel)
                .options(joinedload(GraphDefinitionModel.graph_node_execution_models))
                .where(GraphDefinitionModel.system_role == role)
            )
            res = await session.execute(stmt)
            model = res.unique().scalar_one_or_none()
            if model is None:
                return None
            return self._to_dto(model)

    def _to_dto(self, model: GraphDefinitionModel) -> GraphDefinitionDto:
        return GraphDefinitionDto(
            id=model.id,
            name=model.name,
            purpose=model.purpose,
            graph_node_definitions=[
                GraphNodeDefinitionDto(
                    id=graph_node_definition.id,
                    position=graph_node_definition.position,
                    mode=graph_node_definition.mode,
                    role=graph_node_definition.role,
                    node_type=graph_node_definition.node_type,
                    model=graph_node_definition.model or "",
                    command=graph_node_definition.command,
                    timeout=graph_node_definition.timeout,
                    retries=graph_node_definition.retries,
                    log_level=graph_node_definition.log_level,
                    max_step=graph_node_definition.max_step,
                    no_ask_user=graph_node_definition.no_ask_user or False,
                    autopilot=graph_node_definition.autopilot or False,
                    status_initial=graph_node_definition.status_initial,
                    script=graph_node_definition.script or "",
                    script_type=graph_node_definition.script_type or "",
                )
                for graph_node_definition in model.graph_node_execution_models or []
            ],
        )
