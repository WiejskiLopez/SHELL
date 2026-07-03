from __future__ import annotations

import logging
import math
import struct
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.application.definition.dto.graph_definition import GraphDefinitionDto
from shell.application.definition.dto.graph_node_definition import GraphNodeDefinitionDto
from shell.infrastructure.definition.persistence.sql.models import (
    GraphDefinitionModel,
    GraphNodeDefinitionModel,
    GraphNodeLinkDefinitionModel,
)
from shell.infrastructure.definition.persistence.sql.models.graph_definition_embedding import (
    GraphDefinitionEmbeddingModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell.domain.definition.services.rag_index_service import Embedder

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
        self,
        payload: dict[str, object],
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

            stmt = select(GraphDefinitionModel).where(
                GraphDefinitionModel.id == embedding.graph_definition_id
            )
            res = await session.execute(stmt)
            model = res.unique().scalar_one_or_none()
            if model is None:
                return None
            return await self._to_dto(session, model)

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
            chunk_vec = list(struct.unpack(f"{len(model.embedding) // 4}f", model.embedding))
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
            stmt = select(GraphDefinitionModel).where(
                GraphDefinitionModel.id == definition_id
            )
            res = await session.execute(stmt)
            model = res.unique().scalar_one_or_none()
            if model is None:
                return None
            return await self._to_dto(session, model)

    async def get_graph_definition_by_system_role(
        self,
        role: str,
    ) -> GraphDefinitionDto | None:
        async with self._session_factory() as session:
            stmt = select(GraphDefinitionModel).where(
                GraphDefinitionModel.system_role == role
            )
            res = await session.execute(stmt)
            model = res.unique().scalar_one_or_none()
            if model is None:
                return None
            return await self._to_dto(session, model)

    async def _to_dto(
        self, session: AsyncSession, model: GraphDefinitionModel
    ) -> GraphDefinitionDto:
        link_stmt = (
            select(GraphNodeDefinitionModel)
            .join(
                GraphNodeLinkDefinitionModel,
                GraphNodeLinkDefinitionModel.graph_node_definition_id
                == GraphNodeDefinitionModel.id,
            )
            .where(GraphNodeLinkDefinitionModel.graph_definition_id == model.id)
            .order_by(GraphNodeDefinitionModel.position)
        )
        node_models = (await session.execute(link_stmt)).scalars().all()

        return GraphDefinitionDto(
            id=model.id,
            name=model.name,
            purpose=model.purpose,
            graph_node_definitions=[
                GraphNodeDefinitionDto(
                    id=node.id,
                    position=node.position,
                    mode=node.mode,
                    role=node.role,
                    node_type=node.node_type,
                    model=node.model or "",
                    command=node.command,
                    timeout=node.timeout,
                    retries=node.retries,
                    log_level=node.log_level,
                    max_step=node.max_step,
                    no_ask_user=node.no_ask_user or False,
                    autopilot=node.autopilot or False,
                    status_initial=node.status_initial,
                    script=node.script or "",
                    script_type=node.script_type or "",
                )
                for node in node_models or []
            ],
        )
