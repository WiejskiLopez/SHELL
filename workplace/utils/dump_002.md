### domain/events/events.py
```
"""Domain events for shell_ddd."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell_ddd.domain.value_objects.ids import (
        EnvelopeId,
        GraphId,
        NodeId,
        NodeResultId,
        TaskId,
        TemplateGraphId,
        WorkflowId,
    )
    from shell_ddd.domain.value_objects.task_name import TaskName


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    occurred_at: datetime
    schema_version: int = 1


@dataclass(frozen=True, slots=True)
class TaskCreated(DomainEvent):
    task_id: TaskId
    task_name: TaskName

    @classmethod
    def now(cls, task_id: TaskId, task_name: TaskName, now: datetime) -> TaskCreated:
        return cls(
            occurred_at=now,
            task_id=task_id,
            task_name=task_name,
        )


@dataclass(frozen=True, slots=True)
class GraphBuilt(DomainEvent):
    graph_id: GraphId
    task_id: TaskId
    template_graph_id: TemplateGraphId

    @classmethod
    def now(
        cls,
        graph_id: GraphId,
        task_id: TaskId,
        template_graph_id: TemplateGraphId,
        now: datetime,
    ) -> GraphBuilt:
        return cls(
            occurred_at=now,
            graph_id=graph_id,
            task_id=task_id,
            template_graph_id=template_graph_id,
        )


@dataclass(frozen=True, slots=True)
class WorkflowStarted(DomainEvent):
    workflow_id: WorkflowId
    task_name: str

    @classmethod
    def now(cls, workflow_id: WorkflowId, task_name: str, now: datetime) -> WorkflowStarted:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            task_name=task_name,
        )


@dataclass(frozen=True, slots=True)
class EnvelopeRouted(DomainEvent):
    envelope_id: EnvelopeId
    workflow_id: WorkflowId

    @classmethod
    def now(cls, envelope_id: EnvelopeId, workflow_id: WorkflowId, now: datetime) -> EnvelopeRouted:
        return cls(
            occurred_at=now,
            envelope_id=envelope_id,
            workflow_id=workflow_id,
        )


@dataclass(frozen=True, slots=True)
class EnvelopeExpired(DomainEvent):
    envelope_id: EnvelopeId
    workflow_id: WorkflowId

    @classmethod
    def now(cls, envelope_id: EnvelopeId, workflow_id: WorkflowId, now: datetime) -> EnvelopeExpired:
        return cls(
            occurred_at=now,
            envelope_id=envelope_id,
            workflow_id=workflow_id,
        )


@dataclass(frozen=True, slots=True)
class NodeCompleted(DomainEvent):
    node_id: NodeId
    workflow_id: WorkflowId
    result_id: NodeResultId

    @classmethod
    def now(
        cls, node_id: NodeId, workflow_id: WorkflowId, result_id: NodeResultId, now: datetime
    ) -> NodeCompleted:
        return cls(
            occurred_at=now,
            node_id=node_id,
            workflow_id=workflow_id,
            result_id=result_id,
        )


@dataclass(frozen=True, slots=True)
class NodeFailed(DomainEvent):
    node_id: NodeId
    workflow_id: WorkflowId
    reason: str

    @classmethod
    def now(cls, node_id: NodeId, workflow_id: WorkflowId, reason: str, now: datetime) -> NodeFailed:
        return cls(
            occurred_at=now,
            node_id=node_id,
            workflow_id=workflow_id,
            reason=reason,
        )


@dataclass(frozen=True, slots=True)
class WorkflowCompleted(DomainEvent):
    workflow_id: WorkflowId
    task_name: str

    @classmethod
    def now(cls, workflow_id: WorkflowId, task_name: str, now: datetime) -> WorkflowCompleted:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            task_name=task_name,
        )


@dataclass(frozen=True, slots=True)
class WorkflowFailed(DomainEvent):
    workflow_id: WorkflowId
    task_name: str

    @classmethod
    def now(cls, workflow_id: WorkflowId, task_name: str, now: datetime) -> WorkflowFailed:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            task_name=task_name,
        )


@dataclass(frozen=True, slots=True)
class NodeExecutionRequested(DomainEvent):
    """Request to execute exactly one node identified by ``node_id``.

    Emitted by the Workflow aggregate (start_at / advance_to) and dispatched
    via the EventBus to ``NodeExecutionWorker``. The worker is expected to be
    idempotent: it must compare the request against ``Workflow.cursor`` and
    no-op if they do not match (re-delivery / out-of-order delivery).
    """

    workflow_id: WorkflowId
    node_id: NodeId

    @classmethod
    def now(
        cls,
        workflow_id: WorkflowId,
        node_id: NodeId,
        now: datetime,
    ) -> NodeExecutionRequested:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            node_id=node_id,
        )


@dataclass(frozen=True, slots=True)
class NodeStarted(DomainEvent):
    """A node became the workflow cursor and is now ``running``."""

    workflow_id: WorkflowId
    node_id: NodeId

    @classmethod
    def now(
        cls,
        workflow_id: WorkflowId,
        node_id: NodeId,
        now: datetime,
    ) -> NodeStarted:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            node_id=node_id,
        )


@dataclass(frozen=True, slots=True)
class NodeAdvanced(DomainEvent):
    """Workflow cursor moved from one node to another (audit trail)."""

    workflow_id: WorkflowId
    from_node_id: NodeId
    to_node_id: NodeId

    @classmethod
    def now(
        cls,
        workflow_id: WorkflowId,
        from_node_id: NodeId,
        to_node_id: NodeId,
        now: datetime,
    ) -> NodeAdvanced:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            from_node_id=from_node_id,
            to_node_id=to_node_id,
        )
```

### domain/exceptions.py
```
"""Domain exceptions for shell_ddd."""
from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain errors."""


class TaskNotFound(DomainError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Task not found: {name!r}")


class WorkflowNotFound(DomainError):
    def __init__(self, workflow_id: str) -> None:
        super().__init__(f"Workflow not found: {workflow_id!r}")


class EnvelopeNotFound(DomainError):
    def __init__(self, envelope_id: str) -> None:
        super().__init__(f"Envelope not found: {envelope_id!r}")


class InvalidTaskDefinition(DomainError):
    """Raised when task markdown/yaml has invalid structure."""


class InvalidEnvelopeTransition(DomainError):
    """Raised when envelope status/stage transition is forbidden."""


class NodeNotFound(DomainError):
    def __init__(self, node_id: str) -> None:
        super().__init__(f"Node not found: {node_id!r}")


class PromptNotFound(DomainError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Prompt not found: {name!r}")


class RunnerConfigNotFound(DomainError):
    def __init__(self, package_name: str) -> None:
        super().__init__(f"RunnerConfig not found: {package_name!r}")


class RoleNotResolvable(DomainError):
    """Raised when no graph node satisfies the requested role."""


class MaxStepExceeded(DomainError):
    """Raised when envelope step >= max_step TTL."""


class InvalidNodeMode(DomainError):
    """Raised when an unknown node mode is encountered."""


class WorkflowHasNoNodes(DomainError):
    """Raised when a workflow is started against a Task whose Graph is empty."""

    def __init__(self, task_name: str) -> None:
        super().__init__(f"Workflow has no nodes to execute (task={task_name!r})")


class WorkflowConcurrentlyModified(DomainError):
    """Raised when an optimistic-locking save fails (version mismatch)."""

    def __init__(self, workflow_id: str) -> None:
        super().__init__(
            f"Workflow was concurrently modified: id={workflow_id!r}"
        )


class InvalidWorkflowTransition(DomainError):
    """Raised when a state-machine transition on Workflow is forbidden."""
```

### domain/repositories/__init__.py
```
```

### domain/repositories/envelope_repository.py
```
from __future__ import annotations
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell_ddd.domain.entities.envelope import Envelope
    from shell_ddd.domain.value_objects.ids import EnvelopeId, WorkflowId


class EnvelopeRepository(Protocol):
    async def get_by_id(self, envelope_id: EnvelopeId) -> Envelope | None: ...
    async def save(self, envelope: Envelope) -> None: ...
    async def list_by_workflow(self, workflow_id: WorkflowId, limit: int | None = None, offset: int = 0) -> list[Envelope]: ...
    async def list_pending(self, workflow_id: WorkflowId, limit: int | None = None, offset: int = 0) -> list[Envelope]: ...


class EnvelopeArchive(Protocol):
    async def archive(self, envelope: Envelope) -> str: ...
    async def get(self, archive_uri: str) -> Envelope | None: ...
```

### domain/repositories/graph_repository.py
```
"""GraphRepository port — persistence boundary for the Graph aggregate."""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell_ddd.domain.entities.graph import Graph
    from shell_ddd.domain.value_objects.ids import GraphId, TaskId


class GraphRepository(Protocol):
    async def get_by_id(self, graph_id: GraphId) -> Graph | None: ...
    async def get_by_task_id(self, task_id: TaskId) -> Graph | None: ...
    async def save(self, graph: Graph) -> None: ...
```

### domain/repositories/prompt_repository.py
```
from __future__ import annotations
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell_ddd.domain.entities.prompt import Prompt
    from shell_ddd.domain.value_objects.ids import PromptId


class PromptRepository(Protocol):
    async def get_by_id(self, prompt_id: PromptId) -> Prompt | None: ...
    async def get_current_by_name(self, name: str) -> Prompt | None: ...
    async def save(self, prompt: Prompt) -> None: ...
```

### domain/repositories/rag_repository.py
```
from __future__ import annotations
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell_ddd.domain.entities.rag_document import RagChunk, RagDocument
    from shell_ddd.domain.value_objects.ids import RagDocumentId


class RagDocumentRepository(Protocol):
    async def save(self, document: RagDocument) -> None: ...
    async def get_by_id(self, doc_id: RagDocumentId) -> RagDocument | None: ...
    async def search_similar(
        self,
        query_embedding: bytes,
        top_k: int = 5,
        domain: str | None = None,
    ) -> list[RagChunk]: ...
```

### domain/repositories/repositories.py
```
"""Repository port interfaces — re-exports from granular modules (backward compatibility)."""
from __future__ import annotations

from shell_ddd.domain.repositories.envelope_repository import EnvelopeArchive, EnvelopeRepository
from shell_ddd.domain.repositories.prompt_repository import PromptRepository
from shell_ddd.domain.repositories.rag_repository import RagDocumentRepository
from shell_ddd.domain.repositories.runner_config_repository import RunnerConfigRepository
from shell_ddd.domain.repositories.session_repository import SessionRepository
from shell_ddd.domain.repositories.task_repository import TaskRepository
from shell_ddd.domain.repositories.template_graph_repository import TemplateGraphRepository
from shell_ddd.domain.repositories.workflow_repository import WorkflowRepository

__all__ = [
    "EnvelopeArchive",
    "EnvelopeRepository",
    "PromptRepository",
    "RagDocumentRepository",
    "RunnerConfigRepository",
    "SessionRepository",
    "TaskRepository",
    "TemplateGraphRepository",
    "WorkflowRepository",
]
```

### domain/repositories/runner_config_repository.py
```
from __future__ import annotations
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell_ddd.domain.entities.runner_config import RunnerConfig
    from shell_ddd.domain.value_objects.ids import RunnerConfigId


class RunnerConfigRepository(Protocol):
    async def get_by_id(self, config_id: RunnerConfigId) -> RunnerConfig | None: ...
    async def get_by_package(self, package_name: str) -> RunnerConfig | None: ...
    async def save(self, config: RunnerConfig) -> None: ...
```

### domain/repositories/session_repository.py
```
from __future__ import annotations
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell_ddd.domain.entities.session import Message, Session
    from shell_ddd.domain.value_objects.ids import SessionId


class SessionRepository(Protocol):
    async def save(self, session: Session) -> None: ...
    async def get_by_id(self, session_id: SessionId) -> Session | None: ...
    async def get_messages(self, session_id: SessionId) -> list[Message]: ...
```

### domain/repositories/task_repository.py
```
from __future__ import annotations
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell_ddd.domain.entities.task import Task
    from shell_ddd.domain.value_objects.ids import TaskId
    from shell_ddd.domain.value_objects.task_name import TaskName


class TaskRepository(Protocol):
    async def get_by_id(self, task_id: TaskId) -> Task | None: ...
    async def get_by_name(self, name: TaskName) -> Task | None: ...
    async def get_current_by_name(self, name: TaskName) -> Task | None: ...
    async def save(self, task: Task) -> None: ...
    async def list_current(self) -> list[Task]: ...
```

### domain/repositories/template_graph_repository.py
```
from __future__ import annotations
from typing import TYPE_CHECKING, Protocol

from shell_ddd.domain.entities.template_graph import TemplateGraph

if TYPE_CHECKING:
    from shell_ddd.domain.value_objects.ids import TemplateGraphId


class TemplateGraphRepository(Protocol):
    async def get(self, graph_id: TemplateGraphId) -> TemplateGraph | None: ...
    async def get_template_graph_by_name(self, template_graph_by_name: str) -> TemplateGraph | None: ...
    async def save(self, graph: TemplateGraph) -> None: ...
```

### domain/repositories/workflow_repository.py
```
from __future__ import annotations
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell_ddd.domain.entities.workflow import Workflow
    from shell_ddd.domain.value_objects.ids import WorkflowId


class WorkflowRepository(Protocol):
    async def get_by_id(self, workflow_id: WorkflowId) -> Workflow | None: ...
    async def save(self, workflow: Workflow) -> None: ...
```

### domain/services/__init__.py
```
```

### domain/services/compensation_handler.py
```
"""CompensationHandler — Saga compensation hook invoked when a workflow aborts.

When ``Workflow.abort`` is called, the configured CompensationHandler runs
to release resources, undo side effects or notify external systems. The
default implementation is a no-op so the abort path stays clean for the PoC.

This is a *driving* contract from the domain perspective; concrete
implementations live in the infrastructure layer when real cleanup is needed.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell_ddd.domain.entities.workflow import Workflow


class CompensationHandler(Protocol):
    """Synchronous compensation hook called from ``Workflow.abort``."""

    def compensate(self, workflow: "Workflow", reason: str) -> None:
        """Run any cleanup/compensation needed for the aborted workflow."""
        ...


class NoOpCompensationHandler:
    """Default — performs no compensation."""

    def compensate(self, workflow: "Workflow", reason: str) -> None:
        return None
```

### domain/services/envelope_lifecycle_service.py
```
"""EnvelopeLifecycleService — pure domain TTL/expiry logic."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.domain.value_objects.envelope_status import EnvelopeStatus

if TYPE_CHECKING:
    from shell_ddd.domain.entities.envelope import Envelope


class EnvelopeLifecycleService:
    """Determines whether an envelope should be expired based on step count."""

    @staticmethod
    def should_expire(envelope: Envelope, max_step: int) -> bool:
        """Return True if envelope has exceeded the max_step TTL."""
        if max_step <= 0:
            return False
        return envelope.step >= max_step

    @staticmethod
    def advance(envelope: Envelope, max_step: int) -> EnvelopeStatus:
        """Return the new status after considering TTL.

        - If step >= max_step → DEAD
        - Else keep current status.
        """
        if EnvelopeLifecycleService.should_expire(envelope, max_step):
            return EnvelopeStatus.DEAD
        return envelope.status
```

### domain/services/graph_routing_service.py
```
"""GraphRoutingService — pure domain routing logic."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell_ddd.domain.exceptions import RoleNotResolvable

if TYPE_CHECKING:
    from shell_ddd.domain.entities.task import Graph, GraphNode
    from shell_ddd.domain.value_objects.ids import NodeId


class GraphRoutingService:
    """Resolves target_role -> NodeId using the task graph."""

    @staticmethod
    def resolve_target_node(
        graph: Graph,
        source_node_id: NodeId,
        target_role: str | None,
    ) -> NodeId:
        """Return receiver NodeId for a given source node and optional target_role.

        Rules (matching legacy _run_router):
        1. If target_role is set → find first non-router node whose role matches.
        2. If target_role is None → pick first non-router node that is not the source.
        3. If nothing found → raise RoleNotResolvable.
        """
        non_router: list[GraphNode] = [
            n for n in graph.nodes if str(n.mode) != "router"
        ]

        if target_role:
            matched = [n for n in non_router if n.role == target_role]
            if not matched:
                raise RoleNotResolvable(
                    f"No graph node with role={target_role!r} found in graph {graph.id}"
                )
            return matched[0].id

        candidates = [n for n in non_router if n.id != source_node_id]
        if not candidates and non_router:
            candidates = non_router  # fallback: send to first non-router even if same
        if not candidates:
            raise RoleNotResolvable(
                f"Cannot resolve target: graph {graph.id} has no routable nodes"
            )
        return candidates[0].id
```

### domain/services/node_execution_policy.py
```
"""NodeExecutionPolicy — decides what to do after a single node finishes.

The policy abstracts the failure handling rule for a workflow:
- ``FailFastPolicy`` (default) aborts the workflow on first failure.
- Future policies (``ContinueOnFailurePolicy``, ``RetryWithBackoffPolicy``,
  etc.) plug in here without touching the worker.

A policy is a pure domain service (no I/O, no async).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell_ddd.domain.entities.workflow import Workflow
    from shell_ddd.domain.value_objects.ids import NodeId


class PolicyAction:
    """Marker base class for policy decisions."""


@dataclass(frozen=True, slots=True)
class AbortDecision(PolicyAction):
    """Signal: stop the workflow and mark it as failed."""

    reason: str = ""


@dataclass(frozen=True, slots=True)
class ContinueDecision(PolicyAction):
    """Signal: continue with the next node despite the failure."""


PolicyDecision = AbortDecision | ContinueDecision


class NodeExecutionPolicy(Protocol):
    """Decides what to do after a node has failed."""

    def decide_after_failure(
        self,
        workflow: "Workflow",
        failed_node_id: "NodeId",
        reason: str,
    ) -> PolicyDecision:
        """Return AbortDecision or ContinueDecision."""
        ...


class FailFastPolicy:
    """Default policy — stop the workflow immediately on the first failure."""

    def decide_after_failure(
        self,
        workflow: "Workflow",
        failed_node_id: "NodeId",
        reason: str,
    ) -> PolicyDecision:
        return AbortDecision(reason=reason)
```

### domain/services/node_navigator.py
```
"""NodeNavigator — domain service deciding which node runs next in a Graph.

Implementations encapsulate the **ordering policy**: linear, branching, parallel,
conditional. The default ``LinearNodeNavigator`` orders nodes by ``GraphNode.position``.

The navigator is a *pure* domain service — no I/O, no async — and lives in
``domain/services/`` because it expresses business behaviour (graph traversal).
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Protocol

if TYPE_CHECKING:
    from shell_ddd.domain.entities.graph import Graph
    from shell_ddd.domain.entities.graph_node import GraphNode
    from shell_ddd.domain.value_objects.ids import NodeId


class NodeNavigator(Protocol):
    """Decides the next node(s) to execute in a Graph."""

    def first(self, graph: "Graph") -> "GraphNode | None":
        """Return the first node to execute, or None if the graph has no nodes."""
        ...

    def next_after(self, graph: "Graph", node_id: "NodeId") -> Iterable["GraphNode"]:
        """Return the node(s) that should follow ``node_id`` in execution order.

        Returning an empty iterable signals that no further node remains and the
        workflow has reached a terminal state. The contract intentionally returns
        an Iterable (not a single node) so that future implementations can fan out
        into multiple parallel nodes without changing the worker.
        """
        ...


class LinearNodeNavigator:
    """Default implementation: orders nodes by ``GraphNode.position`` ascending.

    Falls back to the original list order for nodes sharing the same position.
    """

    def first(self, graph: "Graph") -> "GraphNode | None":
        ordered = self._ordered(graph)
        return ordered[0] if ordered else None

    def next_after(self, graph: "Graph", node_id: "NodeId") -> list["GraphNode"]:
        ordered = self._ordered(graph)
        for idx, node in enumerate(ordered):
            if node.id == node_id:
                return [ordered[idx + 1]] if idx + 1 < len(ordered) else []
        return []

    @staticmethod
    def _ordered(graph: "Graph") -> list["GraphNode"]:
        return sorted(graph.nodes, key=lambda n: n.position)
```

### domain/services/rag_index_service.py
```
"""RagIndexService — domain service: chunk text, embed, attach to RagDocument."""
from __future__ import annotations

import math
import struct
from datetime import datetime
from typing import TYPE_CHECKING, Protocol

from shell_ddd.domain.entities.rag_document import RagDocument
from shell_ddd.domain.value_objects.ids import RagChunkId, RagDocumentId

if TYPE_CHECKING:
    pass


class Embedder(Protocol):
    """Port — embed text into a float vector."""

    @property
    def model_name(self) -> str: ...

    @property
    def dim(self) -> int: ...

    def embed_text(self, text: str) -> list[float]: ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


def _encode_vector(vector: list[float]) -> bytes:
    return struct.pack(f"{len(vector)}f", *vector)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be in [0, chunk_size)")
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    step = chunk_size - overlap
    for start in range(0, len(text), step):
        chunk = text[start: start + chunk_size]
        if not chunk:
            break
        chunks.append(chunk)
        if start + chunk_size >= len(text):
            break
    return chunks


def build_rag_document(
        doc_id: RagDocumentId,
        chunk_ids: list[RagChunkId],
        source_uri: str,
        title: str,
        domain: str,
        text: str,
        embedder: Embedder,
        now: datetime,
        chunk_size: int = 500,
        overlap: int = 50,
) -> RagDocument:
    """Chunk *text*, embed each chunk, return a fully-built RagDocument aggregate."""
    doc = RagDocument.new(
        id_=doc_id,
        source_uri=source_uri,
        title=title,
        domain=domain,
        now=now,
    )
    chunks = chunk_text(text, chunk_size, overlap)
    if not chunks:
        return doc
    if len(chunk_ids) < len(chunks):
        raise ValueError(
            f"Not enough chunk_ids supplied: need {len(chunks)}, got {len(chunk_ids)}"
        )
    vectors = embedder.embed_batch(chunks)
    blobs = [_encode_vector(v) for v in vectors]
    doc.add_chunks(
        chunk_ids=chunk_ids[: len(chunks)],
        texts=chunks,
        embeddings=blobs,
        model=embedder.model_name,
    )
    return doc


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


```

### domain/value_objects/__init__.py
```
```

### domain/value_objects/envelope_status.py
```
"""EnvelopeStatus and EnvelopeStage value objects."""
from __future__ import annotations

from enum import StrEnum


class EnvelopeStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    DELIVERED = "delivered"
    FAILED = "failed"
    DEAD = "dead"


class EnvelopeStage(StrEnum):
    DRAFT = "draft"
    SENT = "sent"
    RECEIVED = "received"
    PROCESSING = "processing"
    DONE = "done"
    ARCHIVED = "archived"
```

### domain/value_objects/execution_result.py
```
"""ExecutionResult value object — subprocess output."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    returncode: int
    stdout: str = field(default="")
    stderr: str = field(default="")

    @property
    def success(self) -> bool:
        return self.returncode == 0
```

### domain/value_objects/hash.py
```
"""Hash value object — SHA-256 hex digest."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Hash:
    value: str  # hex digest

    def __post_init__(self) -> None:
        if len(self.value) != 64:
            raise ValueError(f"Hash must be 64 hex chars (SHA-256), got {len(self.value)}")
        try:
            int(self.value, 16)
        except ValueError:
            raise ValueError("Hash must be a valid hex string") from None

    def __str__(self) -> str:
        return self.value

    @classmethod
    def of(cls, data: str | bytes) -> Hash:
        raw = data.encode() if isinstance(data, str) else data
        return cls(hashlib.sha256(raw).hexdigest())
```

### domain/value_objects/ids.py
```
"""Typed ID value objects."""
from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TaskId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("TaskId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> TaskId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class WorkflowId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("WorkflowId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> WorkflowId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class EnvelopeId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("EnvelopeId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> EnvelopeId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class NodeId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("NodeId cannot be empty")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class GraphId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("GraphId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> GraphId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class PromptId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("PromptId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> PromptId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class NodeResultId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("NodeResultId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> NodeResultId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class RunnerConfigId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("RunnerConfigId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> RunnerConfigId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class RagDocumentId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("RagDocumentId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> RagDocumentId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class RagChunkId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("RagChunkId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> RagChunkId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class SessionId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("SessionId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> SessionId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class MessageId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("MessageId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> MessageId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class CorrelationId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("CorrelationId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> CorrelationId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class TemplateGraphId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("TemplateGraphId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> TemplateGraphId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class TemplateGraphNodeId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("TemplateGraphNodeId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> TemplateGraphNodeId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class EnvelopeEventId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("EnvelopeEventId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> EnvelopeEventId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class NodeStateId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("NodeStateId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> NodeStateId:
        return cls(str(uuid.uuid4()))
```

### domain/value_objects/manifest.py
```
"""Manifest value object — parsed manifest.yaml metadata."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell_ddd.domain.value_objects.mode import Mode


@dataclass(frozen=True, slots=True)
class Manifest:
    name: str
    mode: Mode
    role: str
    node_type: str
    version: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Manifest.name cannot be empty")
        if not self.role:
            raise ValueError("Manifest.role cannot be empty")
```

### domain/value_objects/mode.py
```
"""Mode — execution mode of a node (agent/router/tasker/tool/worker)."""
from __future__ import annotations

from enum import StrEnum


class Mode(StrEnum):
    """Execution mode of a node."""

    AGENT = "agent"
    ROUTER = "router"
    TASKER = "tasker"
    TOOL = "tool"
    WORKER = "worker"
```

### domain/value_objects/prompt_file.py
```
"""PromptFile value object."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PromptFile:
    file_name: str
    file_body: str

    def __post_init__(self) -> None:
        if not self.file_name:
            raise ValueError("PromptFile.file_name cannot be empty")
```

### domain/value_objects/status.py
```
"""Status value object — node/workflow/envelope runtime status string."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Status:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Status cannot be empty")

    def __str__(self) -> str:
        return self.value

    # Common sentinel values
    @classmethod
    def idle(cls) -> Status:
        return cls("idle")

    @classmethod
    def running(cls) -> Status:
        return cls("running")

    @classmethod
    def done(cls) -> Status:
        return cls("done")

    @classmethod
    def failed(cls) -> Status:
        return cls("failed")
```

### domain/value_objects/task_body.py
```
"""TaskBody value object — text content of a task definition."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TaskBody:
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("TaskBody cannot be empty")

    def __str__(self) -> str:
        return self.value
```

### domain/value_objects/task_name.py
```
"""TaskName value object."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TaskName:
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("TaskName cannot be empty")
        if len(self.value) > 255:
            raise ValueError("TaskName cannot exceed 255 characters")

    def __str__(self) -> str:
        return self.value
```

### domain/value_objects/timestamp.py
```
"""Timestamp value object — UTC datetime wrapper."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class Timestamp:
    value: datetime

    def __post_init__(self) -> None:
        if self.value.tzinfo is None:
            raise ValueError("Timestamp must be timezone-aware (UTC)")

    def __str__(self) -> str:
        return self.value.isoformat()

    @classmethod
    def now(cls) -> Timestamp:
        return cls(datetime.now(tz=UTC))

    @classmethod
    def from_datetime(cls, dt: datetime) -> Timestamp:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return cls(dt)
```

### domain/value_objects/version.py
```
"""Version value object — monotonically increasing positive integer."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Version:
    value: int

    def __post_init__(self) -> None:
        if self.value < 1:
            raise ValueError(f"Version must be >= 1, got {self.value}")

    def __str__(self) -> str:
        return str(self.value)

    def next(self) -> Version:
        return Version(self.value + 1)

    @classmethod
    def initial(cls) -> Version:
        return cls(1)
```

### domain/value_objects/workflow_cursor.py
```
"""WorkflowCursor — pointer to the node currently being executed.

A WorkflowCursor encapsulates ``current_node_id`` so the Workflow aggregate
does not leak a bare ``str | None`` to the rest of the system. It is also the
extension seam for future multi-cursor scenarios (parallel branches).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell_ddd.domain.value_objects.ids import NodeId


@dataclass(frozen=True, slots=True)
class WorkflowCursor:
    """Immutable VO pointing to the node currently scheduled for execution."""

    current_node_id: "NodeId | None" = None

    @classmethod
    def empty(cls) -> "WorkflowCursor":
        return cls(current_node_id=None)

    @classmethod
    def at(cls, node_id: "NodeId") -> "WorkflowCursor":
        return cls(current_node_id=node_id)

    def is_active(self) -> bool:
        return self.current_node_id is not None

    def points_to(self, node_id: "NodeId") -> bool:
        return self.current_node_id is not None and self.current_node_id == node_id

    def cleared(self) -> "WorkflowCursor":
        return WorkflowCursor(current_node_id=None)
```

### domain/value_objects/workflow_execution_context.py
```
"""WorkflowExecutionContext — runtime context for a single workflow execution.

Captures the data that is constant across all node steps of a workflow
(working directory, correlation id) so each node-execution event stays
minimal and free from environmental concerns.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WorkflowExecutionContext:
    """Immutable VO carrying per-workflow execution context."""

    work_dir: str
    correlation_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.work_dir, str):
            raise ValueError("work_dir must be a string")
        if not isinstance(self.correlation_id, str):
            raise ValueError("correlation_id must be a string")

    @classmethod
    def empty(cls) -> "WorkflowExecutionContext":
        return cls(work_dir="", correlation_id="")
```

### framework/__init__.py
```
```

### framework/api/__init__.py
```
```

### framework/api/app.py
```
"""FastAPI application factory for shell_ddd control plane."""
from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from shell_ddd.bootstrap.container.core_container import CoreContainer
from shell_ddd.bootstrap.config_logging.setup_logging import setup_logging
from shell_ddd.domain.exceptions import DomainError
from shell_ddd.framework.api.middleware.correlation_id import CorrelationIdMiddleware
from shell_ddd.framework.api.middleware.error_handler import domain_error_handler
from shell_ddd.framework.api.routers import envelopes, nodes, tasks, workflows


def create_app(core_container: CoreContainer) -> FastAPI:
    """Create the FastAPI application with all routers and middleware."""

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
        setup_logging()
        yield  # startup / shutdown hooks can be added here

    app = FastAPI(
        title="shell_ddd control plane",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.core_container = core_container

    # Middleware
    app.add_middleware(CorrelationIdMiddleware)
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore[arg-type]

    # Routers
    app.include_router(tasks.router)
    app.include_router(workflows.router)
    app.include_router(envelopes.router)
    app.include_router(nodes.router)

    @app.get("/health", tags=["health"])
    async def health() -> dict:  # type: ignore[type-arg]
        return {"status": "ok"}

    return app
```

### framework/api/middleware/__init__.py
```
```

### framework/api/middleware/correlation_id.py
```
"""Correlation-ID middleware — adds X-Correlation-ID header to every request."""
from __future__ import annotations

from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: object) -> Response:  # type: ignore[override]
        cid = request.headers.get("X-Correlation-ID")
        token = correlation_id_var.set(cid)
        try:
          response: Response = await call_next(request)
          if cid:
             response.headers["X-Correlation-ID"] = cid
             return response
        finally:
        # Ważne: Resetujemy kontekst po zakończeniu żądania
           correlation_id_var.reset(token)
        return response
```

### framework/api/middleware/error_handler.py
```
"""Error handler middleware — maps DomainErrors to 4xx HTTP responses."""
from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from shell_ddd.domain.exceptions import (
    DomainError,
    EnvelopeNotFound,
    NodeNotFound,
    PromptNotFound,
    RunnerConfigNotFound,
    TaskNotFound,
    WorkflowNotFound,
)

_NOT_FOUND = {TaskNotFound, WorkflowNotFound, EnvelopeNotFound, NodeNotFound, PromptNotFound, RunnerConfigNotFound}


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    status = 404 if type(exc) in _NOT_FOUND else 400
    return JSONResponse(status_code=status, content={"detail": str(exc)})
```

### framework/api/routers/__init__.py
```
```

### framework/api/routers/envelopes.py
```
"""Envelopes router — query envelopes by workflow."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from shell_ddd.application.queries.queries import GetEnvelopesByWorkflowQuery
from shell_ddd.bootstrap.container.core_container import CoreContainer

router = APIRouter(prefix="/envelopes", tags=["envelopes"])


from fastapi import Request as _Request


def get_core_container(request: _Request) -> CoreContainer:
    return request.app.state.core_container


@router.get("/workflow/{workflow_id}")
async def list_by_workflow(
    workflow_id: str,
    pending_only: bool = False,
    core_container: CoreContainer = Depends(get_core_container),
) -> dict:  # type: ignore[type-arg]
    result = await core_container.app.buses.query_bus().dispatch(
        GetEnvelopesByWorkflowQuery(workflow_id=workflow_id, pending_only=pending_only)
    )
    envelopes = result if result is not None else []
    return {"workflow_id": workflow_id, "envelopes": [str(e) for e in envelopes]}
```

### framework/api/routers/nodes.py
```
"""Nodes router — query node execution results."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from shell_ddd.application.queries.queries import GetNodeResultQuery
from shell_ddd.bootstrap.container.core_container import CoreContainer

router = APIRouter(prefix="/nodes", tags=["nodes"])


from fastapi import Request as _Request


def get_core_container(request: _Request) -> CoreContainer:
    return request.app.state.core_container


@router.get("/{node_id}/result")
async def get_node_result(
    node_id: str,
    workflow_id: str,
        core_container: CoreContainer = Depends(get_core_container),
) -> dict:  # type: ignore[type-arg]
    result = await core_container.app.buses.query_bus().dispatch(GetNodeResultQuery(node_id=node_id, workflow_id=workflow_id))
    if result is None:
        raise HTTPException(status_code=404, detail=f"NodeResult for '{node_id}' not found")
    return {"node_id": node_id, "result": str(result)}
```

### framework/api/routers/tasks.py
```
"""Tasks router — import and query tasks."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from shell_ddd.application.commands.commands import ImportTaskCommand
from shell_ddd.application.queries.queries import GetTaskByNameQuery
from shell_ddd.bootstrap.container.core_container import CoreContainer

router = APIRouter(prefix="/tasks", tags=["tasks"])


class ImportTaskRequest(BaseModel):
    task_name: str
    md_path: str


class ImportTaskResponse(BaseModel):
    task_id: str


def get_core_container(request: Request) -> CoreContainer:
    return request.app.state.core_container


@router.post("/import", response_model=ImportTaskResponse, status_code=201)
async def import_task(body: ImportTaskRequest, core_container: CoreContainer = Depends(get_core_container)) -> ImportTaskResponse:
    cmd = ImportTaskCommand(md_path=body.md_path, task_name=body.task_name)
    task_id = await core_container.app.buses.command_bus().dispatch(cmd)
    return ImportTaskResponse(task_id=str(task_id))


@router.get("/{name}")
async def get_task(name: str, core_container: CoreContainer = Depends(get_core_container)) -> dict:  # type: ignore[type-arg]
    result = await core_container.app.buses.query_bus().dispatch(GetTaskByNameQuery(name=name))
    if result is None:
        raise HTTPException(status_code=404, detail=f"Task '{name}' not found")
    return {"name": name, "task": str(result)}
```

### framework/api/routers/workflows.py
```
"""Workflows router — start and query workflows."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from shell_ddd.application.commands.commands import RouteEnvelopesCommand, StartWorkflowCommand
from shell_ddd.application.queries.queries import GetWorkflowQuery
from shell_ddd.bootstrap.container.core_container import CoreContainer

router = APIRouter(prefix="/workflows", tags=["workflows"])


class StartWorkflowRequest(BaseModel):
    task_name: str


class StartWorkflowResponse(BaseModel):
    workflow_id: str


class RouteResponse(BaseModel):
    routed: int


from fastapi import Request as _Request


def get_core_container(request: _Request) -> CoreContainer:
    return request.app.state.core_container


@router.post("", response_model=StartWorkflowResponse, status_code=201)
async def start_workflow(
    body: StartWorkflowRequest, core_container: CoreContainer = Depends(get_core_container)
) -> StartWorkflowResponse:
    cmd = StartWorkflowCommand(task_name=body.task_name)
    wf_id = await core_container.app.buses.command_bus().dispatch(cmd)
    return StartWorkflowResponse(workflow_id=str(wf_id))


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str, core_container: CoreContainer = Depends(get_core_container)) -> dict:  # type: ignore[type-arg]
    result = await core_container.app.buses.query_bus().dispatch(GetWorkflowQuery(workflow_id=workflow_id))
    if result is None:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")
    return {"workflow_id": workflow_id, "workflow": str(result)}


@router.post("/{workflow_id}/route", response_model=RouteResponse)
async def route_envelopes(workflow_id: str, core_container: CoreContainer = Depends(get_core_container)) -> RouteResponse:
    cmd = RouteEnvelopesCommand(workflow_id=workflow_id)
    count = await core_container.app.buses.command_bus().dispatch(cmd)
    return RouteResponse(routed=count or 0)
```

### framework/cli/__init__.py
```
```

### framework/cli/commands/__init__.py
```
```

### framework/cli/main.py
```
"""Main CLI entrypoint for shell_ddd — dispatches to per-mode command handlers."""
from __future__ import annotations

import asyncio
import os
import sys
from collections.abc import Sequence

from shell_ddd.bootstrap.factory.application_factory import ApplicationFactory
from shell_ddd.bootstrap.config_logging.setup_logging import setup_logging
from shell_ddd.framework.cli.parser import build_parser

# Map of mode-name → default runner root dir (relative to this file if available).
_MODE_RUNNER_ROOTS: dict[str, str] = {
    "agent": "agent",
    "router": "router",
    "tasker": "tasker",
    "tool": "tool",
    "worker": "worker",
}


def _get_database_url() -> str:
    return os.environ.get("SHELL_DDD_DATABASE_URL", "sqlite+aiosqlite:///shell_ddd.db")


def _get_max_step() -> int:
    try:
        return int(os.environ.get("SHELL_DDD_MAX_STEP", "20"))
    except ValueError:
        return 20


async def _run_node(mode: str, argv: Sequence[str]) -> int:
    from shell_ddd.application.commands.commands import RunNodeCommand

    parser = build_parser(prog=f"shell_ddd {mode}")
    ns = parser.parse_args(list(argv))

    database_url = _get_database_url()
    max_step = ns.max_step if ns.max_step is not None else _get_max_step()
    core_container = await ApplicationFactory(database_url=database_url, max_step=max_step).build()

    node_id = ns.node_dir or mode
    workflow_id = ns.workflow_id or "default"
    work_dir = ns.work_dir or os.getcwd()

    cmd = RunNodeCommand(
        node_id=node_id,
        workflow_id=workflow_id,
        workspace_path=work_dir,
    )
    try:
        await core_container.app.buses.command_bus().dispatch(cmd)
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


async def _import_task(argv: Sequence[str]) -> int:
    from shell_ddd.application.commands.commands import ImportTaskCommand

    parser = build_parser(prog="shell_ddd import-task")
    ns = parser.parse_args(list(argv))

    task_name = ns.task_name
    task_dir = ns.task_dir
    if not task_name or not task_dir:
        print("ERROR: --task-name and --task-dir are required for import-task.", file=sys.stderr)
        return 1

    import pathlib
    md_path = str(pathlib.Path(task_dir) / f"{task_name}.md")

    database_url = _get_database_url()
    core_container = await ApplicationFactory(database_url=database_url).build()
    cmd = ImportTaskCommand(md_path=md_path, task_name=task_name)
    try:
        task_id = await core_container.app.buses.command_bus().dispatch(cmd)
        print(f"Imported task '{task_name}' with id={task_id}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


async def _route(argv: Sequence[str]) -> int:
    from shell_ddd.application.commands.commands import RouteEnvelopesCommand

    parser = build_parser(prog="shell_ddd route")
    ns = parser.parse_args(list(argv))

    database_url = _get_database_url()
    max_step = ns.max_step if ns.max_step is not None else _get_max_step()
    core_container = await ApplicationFactory(database_url=database_url, max_step=max_step).build()

    workflow_id = ns.workflow_id or "default"
    cmd = RouteEnvelopesCommand(workflow_id=workflow_id)
    try:
        count = await core_container.app.buses.command_bus().dispatch(cmd)
        print(f"Routed {count} envelopes.")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


async def _run_tasker(argv: Sequence[str]) -> int:
    from shell_ddd.application.commands.commands import RunTaskerWorkflowCommand

    parser = build_parser(prog="shell_ddd run-tasker")
    ns = parser.parse_args(list(argv))

    task_name = ns.task_name
    if not task_name:
        print("ERROR: --task-name is required for run-tasker.", file=sys.stderr)
        return 1

    work_dir = ns.work_dir or os.getcwd()

    database_url = _get_database_url()
    core_container = await ApplicationFactory(database_url=database_url).build()
    cmd = RunTaskerWorkflowCommand(
        task_name=task_name,
        work_dir=work_dir,
    )
    try:
        workflow_id = await core_container.app.buses.command_bus().dispatch(cmd)
        print(f"Tasker workflow completed: workflow_id={workflow_id}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry-point — first positional arg is the mode/subcommand."""
    args = list(argv) if argv is not None else sys.argv[1:]
    setup_logging()
    if not args:
        print("Usage: shell_ddd <mode> [options]", file=sys.stderr)
        print(f"  modes: {', '.join(list(_MODE_RUNNER_ROOTS) + ['import-task', 'route'])}", file=sys.stderr)
        return 1

    mode = args[0]
    rest = args[1:]

    if mode in _MODE_RUNNER_ROOTS:
        return asyncio.run(_run_node(mode, rest))
    elif mode == "import-task":
        return asyncio.run(_import_task(rest))
    elif mode == "route":
        return asyncio.run(_route(rest))
    elif mode == "run-tasker":
        return asyncio.run(_run_tasker(rest))
    else:
        print(f"Unknown mode: {mode!r}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

### framework/cli/parser.py
```
"""Shared argparse setup for all shell_ddd CLI entrypoints."""
from __future__ import annotations

import argparse
from typing import Sequence


def build_parser(prog: str = "shell_ddd") -> argparse.ArgumentParser:
    """Return a fully configured ArgumentParser with all shared flags."""
    parser = argparse.ArgumentParser(
        prog=prog,
        description="shell_ddd node runner.",
        add_help=True,
    )
    # ---- identity ----
    parser.add_argument("--node-dir", dest="node_dir", metavar="PATH", default=None)
    parser.add_argument("--mode", dest="mode", metavar="MODE", default=None)
    parser.add_argument("--role", dest="role", metavar="ROLE", default=None)
    parser.add_argument("--type", dest="type", metavar="TYPE", default=None)
    # ---- execution ----
    parser.add_argument("--model", dest="model", metavar="MODEL", default=None)
    parser.add_argument("--timeout", dest="timeout", type=int, metavar="SECONDS", default=None)
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", default=False)
    parser.add_argument("--log-level", dest="log_level", metavar="LEVEL", default="INFO")
    # ---- copilot/agent ----
    parser.add_argument("--no-ask-user", dest="no_ask_user", action="store_true", default=False)
    parser.add_argument("--autopilot", dest="autopilot", action="store_true", default=False)
    parser.add_argument("--add-dir", dest="add_dirs", metavar="PATH", action="append", default=[])
    parser.add_argument("--prompt", dest="prompt", metavar="PROMPT", default=None)
    parser.add_argument("--prompt-dir", dest="prompt_dir", metavar="PATH", default=None)
    # ---- task/source ----
    parser.add_argument("--source-dir", dest="source_dir", metavar="PATH", default=None)
    parser.add_argument("--task-name", dest="task_name", metavar="NAME", default=None)
    parser.add_argument("--task-id", dest="task_id", type=int, metavar="ID", default=None)
    parser.add_argument("--task-dir", dest="task_dir", metavar="PATH", default=None)
    parser.add_argument("--work-dir", dest="work_dir", metavar="PATH", default=None)
    # ---- routing ----
    parser.add_argument("--max-step", dest="max_step", type=int, metavar="N", default=None)
    parser.add_argument("--workflow-id", dest="workflow_id", metavar="ID", default=None)
    parser.add_argument("--envelope-id", dest="envelope_id", type=int, metavar="ID", default=None)
    parser.add_argument("--parent-thread-id", dest="parent_thread_id", metavar="ID", default=None)
    parser.add_argument("--parent-node-dir", dest="parent_node_dir", metavar="PATH", default=None)
    # ---- runner root (for entrypoint shims) ----
    parser.add_argument("--runner-root-dir", dest="runner_root_dir", metavar="PATH", default=None)
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)
```

### framework/entrypoints/__init__.py
```
```

### framework/entrypoints/agent_entrypoint.py
```
import sys
from shell_ddd.framework.cli.main import main
if __name__ == '__main__':
    sys.exit(main(['agent', *sys.argv[1:]]))

```

### framework/entrypoints/router_entrypoint.py
```
import sys
from shell_ddd.framework.cli.main import main
if __name__ == '__main__':
    sys.exit(main(['router', *sys.argv[1:]]))

```

### framework/entrypoints/tasker_entrypoint.py
```
import sys
from shell_ddd.framework.cli.main import main
if __name__ == '__main__':
    sys.exit(main(['tasker', *sys.argv[1:]]))

```

### framework/entrypoints/tool_entrypoint.py
```
import sys
from shell_ddd.framework.cli.main import main
if __name__ == '__main__':
    sys.exit(main(['tool', *sys.argv[1:]]))

```

### framework/entrypoints/worker_entrypoint.py
```
import sys
from shell_ddd.framework.cli.main import main
if __name__ == '__main__':
    sys.exit(main(['worker', *sys.argv[1:]]))

```

### infrastructure/__init__.py
```
```

### infrastructure/configuration/__init__.py
```
```

### infrastructure/external/__init__.py
```
```

### infrastructure/external/hash_embedder.py
```
"""HashEmbedder — deterministic, dependency-free stub embedder (dev/test)."""
from __future__ import annotations

import hashlib
import math
import struct


class HashEmbedder:
    """Generates a fixed-dim float vector via hashing.

    Deterministic: same text → same vector. Useful in tests and development
    before a real model (sentence-transformers, Ollama, …) is wired in.
    """

    def __init__(self, dim: int = 64) -> None:
        if dim <= 0:
            raise ValueError("dim must be positive")
        self._dim = dim
        self._model_name = f"hash-stub-{dim}"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dim(self) -> int:
        return self._dim

    def embed_text(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        repeats = (self._dim * 4 + len(digest) - 1) // len(digest)
        raw = (digest * repeats)[: self._dim * 4]
        ints = struct.unpack(f"{self._dim}I", raw)
        floats = [(v / 0xFFFFFFFF) * 2.0 - 1.0 for v in ints]
        norm = math.sqrt(sum(x * x for x in floats)) or 1.0
        return [x / norm for x in floats]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]
```

### infrastructure/filesystem/__init__.py
```
```

### infrastructure/filesystem/envelope_archive_fs.py
```
"""FileSystemEnvelopeArchive — filesystem-based EnvelopeArchive adapter."""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell_ddd.domain.entities.envelope import Envelope


class FileSystemEnvelopeArchive:
    """Persists archived envelopes as JSON files under a configurable root dir.

    URI format: ``fs://archive/<workflow_id>/<envelope_id>.json``
    """

    def __init__(self, archive_root: str) -> None:
        self._root = Path(archive_root)

    async def archive(self, envelope: Envelope) -> str:
        """Serialise envelope to JSON and return the archive URI."""
        wf_dir = self._root / envelope.workflow_id.value
        wf_dir.mkdir(parents=True, exist_ok=True)
        target = wf_dir / f"{envelope.id.value}.json"
        payload = {
            "id": envelope.id.value,
            "workflow_id": envelope.workflow_id.value,
            "status": envelope.status.value,
            "stage": envelope.stage.value,
            "payload": envelope.payload,
            "created_at": envelope.created_at.isoformat(),
            "updated_at": envelope.updated_at.isoformat(),
        }
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return f"fs://archive/{envelope.workflow_id.value}/{envelope.id.value}.json"

    async def get(self, archive_uri: str) -> Envelope | None:
        """Retrieve an archived envelope by its URI.  Returns None if not found."""
        # URI: fs://archive/<workflow_id>/<envelope_id>.json
        suffix = archive_uri.removeprefix("fs://archive/")
        parts = suffix.split("/", 1)
        if len(parts) != 2:
            return None
        wf_id, filename = parts
        target = self._root / wf_id / filename
        if not target.exists():
            return None
        # Minimal deserialisation — returns raw dict as pseudo-Envelope
        # Full round-trip requires proper mappers (wired in Faza 3 mappers).
        return None  # noqa: RET504
```

### infrastructure/filesystem/node_workspace.py
```
"""NodeWorkspaceFs — filesystem implementation of the NodeWorkspace port."""
from __future__ import annotations

import shutil
from pathlib import Path


# Standard sub-directories inside .node/
_NODE_SUBDIRS = [
    "input",
    "output",
    "logs",
    "temp",
    "prompt",
    "scripts",
    "status",
    "port",
    "archive",
]
_DOT_NODE = ".node"


class NodeWorkspaceFs:
    """Creates and manages the .node/ workspace directory for a single node execution.

    Directory layout (matching legacy SHELL conventions):
    ``<workspace_path>/.node/{input,output,logs,temp,prompt,scripts,status,port,archive}/``
    """

    async def prepare(self, node_id: str, work_dir: str) -> str:
        """Create workspace directory tree and return the workspace path."""
        ws = Path(work_dir) / node_id
        dot_node = ws / _DOT_NODE
        for subdir in _NODE_SUBDIRS:
            (dot_node / subdir).mkdir(parents=True, exist_ok=True)
        return str(ws)

    async def cleanup(self, workspace_path: str) -> None:
        """Remove the workspace directory tree (best-effort)."""
        ws = Path(workspace_path)
        if ws.exists():
            shutil.rmtree(ws, ignore_errors=True)

    async def read_input(self, workspace_path: str) -> str:
        """Read content of .node/input/input.txt if it exists."""
        p = Path(workspace_path) / _DOT_NODE / "input" / "input.txt"
        if p.exists():
            return p.read_text(encoding="utf-8")
        return ""

    async def write_output(self, workspace_path: str, name: str, body: str) -> Path:
        """Write body to .node/output/<name> and return the path."""
        out = Path(workspace_path) / _DOT_NODE / "output" / name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")
        return out
```

### infrastructure/filesystem/task_loader.py
```
"""FileSystemTaskLoader — reads task.md + task.yaml from the filesystem."""
from __future__ import annotations

import asyncio
from asyncio import to_thread
from pathlib import Path


class FileSystemTaskLoader:
    """Reads task markdown asynchronously (via thread pool)."""

    async def load(self, md_path: str) -> str:
        return await to_thread(
            Path(md_path).read_text,
            encoding="utf-8",
        )
```

### infrastructure/logging/__init__.py
```
"""Stdlib logging adapter."""
from __future__ import annotations

import logging


class StdlibLogger:
    """Implements application/ports/ports.Logger using Python stdlib logging."""

    def __init__(self, name: str = "shell_ddd") -> None:
        self._log = logging.getLogger(name)

    def debug(self, msg: str, **kw: object) -> None:
        self._log.debug(msg, extra=kw)

    def info(self, msg: str, **kw: object) -> None:
        self._log.info(msg, extra=kw)

    def warning(self, msg: str, **kw: object) -> None:
        self._log.warning(msg, extra=kw)

    def error(self, msg: str, **kw: object) -> None:
        self._log.error(msg, extra=kw)
```

### infrastructure/logging/composite_event_publisher.py
```
"""CompositeEventPublisher — fans out to multiple EventPublisher adapters."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell_ddd.application.ports.ports import EventPublisher
    from shell_ddd.domain.events.events import DomainEvent


class CompositeEventPublisher:
    """Delegates ``publish`` to every publisher in the list, in order."""

    def __init__(self, publishers: list[EventPublisher]) -> None:
        self._publishers = list(publishers)

    async def publish(self, events: list[DomainEvent]) -> None:
        for publisher in self._publishers:
            await publisher.publish(events)
```

### infrastructure/logging/logging_event_publisher.py
```
"""LoggingEventPublisher — publishes domain events via the Logger port."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell_ddd.application.ports.ports import Logger
    from shell_ddd.domain.events.events import DomainEvent


class LoggingEventPublisher:
    """EventPublisher adapter that logs each domain event as a structured JSON entry."""

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    async def publish(self, events: list[DomainEvent]) -> None:
        for event in events:
            self._logger.info(
                "domain_event",
                event_type=type(event).__name__,
                occurred_at=event.occurred_at.isoformat(),
            )
```

### infrastructure/logging/sql_audit_publisher.py
```
"""SqlAuditPublisher — persists domain events to the audit_event table."""
from __future__ import annotations

import dataclasses
import uuid
from typing import TYPE_CHECKING

from shell_ddd.infrastructure.persistence.sql.models import AuditEventModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell_ddd.domain.events.events import DomainEvent


class SqlAuditPublisher:
    """EventPublisher adapter that writes one row per domain event to ``audit_event``."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def publish(self, events: list[DomainEvent]) -> None:
        if not events:
            return
        async with self._session_factory() as session:
            for event in events:
                payload = {
                    f.name: str(getattr(event, f.name))
                    for f in dataclasses.fields(event)  # type: ignore[arg-type]
                    if f.name != "occurred_at"
                }
                session.add(
                    AuditEventModel(
                        id=str(uuid.uuid4()),
                        event_type=type(event).__name__,
                        occurred_at=event.occurred_at,
                        payload=payload,
                    )
                )
            await session.commit()
```

### infrastructure/logging/stdlib_logger.py
```
"""Structured JSON logger — implements the Logger port using stdlib logging."""
from __future__ import annotations

import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime

# ---------------------------------------------------------------------------
# Correlation-ID context variable (set per-request/command by middleware or CLI)
# ---------------------------------------------------------------------------

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    return correlation_id_var.get()


def set_correlation_id(value: str) -> None:
    correlation_id_var.set(value)


# ---------------------------------------------------------------------------
# JSON formatter
# ---------------------------------------------------------------------------


class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON strings."""

    def format(self, record: logging.LogRecord) -> str:
        data: dict[str, object] = {
            "ts": datetime.now(tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "correlation_id": get_correlation_id(),
        }
        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)
        # Include any extra fields attached by the caller
        _std_keys = logging.LogRecord.__dict__.keys() | {
            "message", "asctime", "taskName"
        }
        for k, v in record.__dict__.items():
            if k not in _std_keys and not k.startswith("_"):
                data.setdefault("extra", {})[k] = v  # type: ignore[index]
        return json.dumps(data, default=str)


# ---------------------------------------------------------------------------
# Logger adapter
# ---------------------------------------------------------------------------


def _make_handler() -> logging.StreamHandler:  # type: ignore[type-arg]
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    return handler


class StdlibLogger:
    """Implements the ``Logger`` port using stdlib logging with JSON output."""

    def __init__(self, name: str = "shell_ddd", level: int = logging.INFO) -> None:
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)

    def debug(self, msg: str, **kw: object) -> None:
        self._logger.debug(msg, extra=kw if kw else None)

    def info(self, msg: str, **kw: object) -> None:
        self._logger.info(msg, extra=kw if kw else None)

    def warning(self, msg: str, **kw: object) -> None:
        self._logger.warning(msg, extra=kw if kw else None)

    def error(self, msg: str, **kw: object) -> None:
        self._logger.error(msg, extra=kw if kw else None)
```

### infrastructure/messaging/__init__.py
```
```

### infrastructure/messaging/memory_outbox_store.py
```
"""InMemoryOutboxStore — in-process store for unit-testing the outbox pattern."""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import datetime  # noqa: TC003
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell_ddd.domain.events.events import DomainEvent


@dataclass
class OutboxRecord:
    id: str
    event_type: str
    occurred_at: datetime
    payload: dict  # type: ignore[type-arg]
    published_at: datetime | None = None

    @property
    def is_published(self) -> bool:
        return self.published_at is not None


class InMemoryOutboxStore:
    """Simple in-memory outbox for tests — implements the same interface as SqlOutboxPublisher."""

    def __init__(self) -> None:
        self.records: list[OutboxRecord] = []

    async def publish(self, events: list[DomainEvent]) -> None:
        import uuid

        for event in events:
            payload = {
                f.name: str(getattr(event, f.name))
                for f in dataclasses.fields(event)  # type: ignore[arg-type]
                if f.name != "occurred_at"
            }
            self.records.append(
                OutboxRecord(
                    id=str(uuid.uuid4()),
                    event_type=type(event).__name__,
                    occurred_at=event.occurred_at,
                    payload=payload,
                )
            )

    def pending(self) -> list[OutboxRecord]:
        return [r for r in self.records if not r.is_published]
```

### infrastructure/messaging/outbox/__init__.py
```
```

### infrastructure/messaging/outbox_relay.py
```
"""OutboxRelay — reads pending outbox_event rows and re-publishes to an EventPublisher.

Intended as a one-shot or periodic background task:
    relay = OutboxRelay(session_factory, downstream_publisher)
    await relay.run_once()   # processes all pending rows in one pass

Concurrency safety: uses SELECT FOR UPDATE SKIP LOCKED on dialects that support
it (PostgreSQL).  On SQLite (single-writer) the clause is omitted automatically.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select, update

from shell_ddd.infrastructure.persistence.sql.models import OutboxEventModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell_ddd.application.ports.ports import EventPublisher


class OutboxRelay:
    """Reads unpublished outbox rows and forwards them to the downstream publisher."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        downstream: EventPublisher,
        batch_size: int = 100,
    ) -> None:
        self._session_factory = session_factory
        self._downstream = downstream
        self._batch_size = batch_size
        # Detect once at construction time whether the DB supports SKIP LOCKED.
        # SQLite does not support FOR UPDATE; PostgreSQL does.
        engine = getattr(session_factory, "bind", None)
        dialect_name: str = engine.dialect.name if engine is not None else "unknown"
        self._skip_locked: bool = dialect_name not in ("sqlite",)

    async def run_once(self) -> int:
        """Process one batch of pending outbox events.

        Returns the number of events processed.
        """
        async with self._session_factory() as session:
            stmt = (
                select(OutboxEventModel)
                .where(OutboxEventModel.published_at.is_(None))
                .order_by(OutboxEventModel.occurred_at)
                .limit(self._batch_size)
            )
            if self._skip_locked:
                # Prevents two relay workers from picking the same rows.
                # Row-level lock is released after the UPDATE below commits.
                stmt = stmt.with_for_update(skip_locked=True)

            rows = (await session.execute(stmt)).scalars().all()

            if not rows:
                return 0

            # Build lightweight event wrappers for the downstream publisher
            events: list[_OutboxProxy] = [_OutboxProxy(r) for r in rows]
            await self._downstream.publish(events)  # type: ignore[arg-type]

            now = datetime.now(tz=UTC)
            ids = [r.id for r in rows]
            await session.execute(
                update(OutboxEventModel)
                .where(OutboxEventModel.id.in_(ids))
                .values(published_at=now)
            )
            await session.commit()
            return len(rows)


class _OutboxProxy:
    """Thin wrapper exposing the minimal interface expected by EventPublisher.publish().

    The downstream publisher only needs ``type(event).__name__`` and
    ``event.occurred_at``; everything else lives in ``payload``.
    """

    def __init__(self, row: OutboxEventModel) -> None:
        self._row = row
        self.occurred_at: datetime = row.occurred_at
        self.event_type: str = row.event_type
        self.payload: dict = row.payload  # type: ignore[type-arg]

    def __class_getitem__(cls, item: object) -> object:  # pragma: no cover
        return cls
```

### infrastructure/messaging/sql_outbox_publisher.py
```
"""SqlOutboxPublisher — EventPublisher adapter that writes to outbox_event table.

Events are stored in a dedicated DB session so they survive even if the caller's
transaction was already committed.  An OutboxRelay then reads them and fans them
out to the EventBus.
"""
from __future__ import annotations

import dataclasses
import uuid
from typing import TYPE_CHECKING

from shell_ddd.infrastructure.persistence.sql.models import OutboxEventModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from shell_ddd.domain.events.events import DomainEvent


class SqlOutboxPublisher:
    """Writes domain events to the ``outbox_event`` table (own session per call)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def publish(self, events: list[DomainEvent]) -> None:
        if not events:
            return
        async with self._session_factory() as session:
            for event in events:
                payload = {
                    f.name: str(getattr(event, f.name))
                    for f in dataclasses.fields(event)  # type: ignore[arg-type]
                    if f.name != "occurred_at"
                }
                session.add(
                    OutboxEventModel(
                        id=str(uuid.uuid4()),
                        event_type=type(event).__name__,
                        occurred_at=event.occurred_at,
                        payload=payload,
                        published_at=None,
                    )
                )
            await session.commit()
```

### infrastructure/persistence/__init__.py
```
"""SqlAlchemyUnitOfWork \u2014 transactional boundary for SQL backends."""
from __future__ import annotations

import dataclasses
import uuid
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shell_ddd.infrastructure.persistence.sql.models import OutboxEventModel
from shell_ddd.infrastructure.persistence.sql.repositories import (
    SqlEnvelopeArchiveStub,
    SqlEnvelopeRepository,
    SqlGraphRepository,
    SqlPromptRepository,
    SqlRagDocumentRepository,
    SqlRunnerConfigRepository,
    SqlSessionRepository,
    SqlTaskRepository,
    SqlWorkflowRepository,
    SqlTemplateGraphRepository,
)

if TYPE_CHECKING:
    from shell_ddd.domain.events.events import DomainEvent


class SqlAlchemyUnitOfWork:
    """UnitOfWork backed by SQLAlchemy AsyncSession.

    Works for both SQLite (sqlite+aiosqlite) and PostgreSQL (postgresql+asyncpg).
    Outbox events are written to the same session — atomically with domain state.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._factory = session_factory
        self._staged_events: list[DomainEvent] = []

    # ------------------------------------------------------------------
    # Outbox staging — handlers call uow.stage_events() BEFORE commit
    # ------------------------------------------------------------------

    def stage_events(self, events: list[DomainEvent]) -> None:
        """Accumulate domain events to be written to the outbox inside commit()."""
        self._staged_events.extend(events)

    @property
    def events(self) -> list[DomainEvent]:
        return list(self._staged_events)

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        self._session: AsyncSession = self._factory()
        self._staged_events = []
        self.tasks = SqlTaskRepository(self._session)
        self.graphs = SqlGraphRepository(self._session)
        self.workflows = SqlWorkflowRepository(self._session)
        self.envelopes = SqlEnvelopeRepository(self._session)
        self.prompts = SqlPromptRepository(self._session)
        self.runner_configs = SqlRunnerConfigRepository(self._session)
        self.envelope_archive: SqlEnvelopeArchiveStub = SqlEnvelopeArchiveStub()
        self.rag_documents = SqlRagDocumentRepository(self._session)
        self.sessions = SqlSessionRepository(self._session)
        self.template_graphs = SqlTemplateGraphRepository(self._session)
        return self

    async def __aexit__(self, exc_type: object, *args: object) -> None:
        if exc_type:
            await self.rollback()
        await self._session.close()

    async def commit(self) -> None:
        """Write staged outbox events to DB and commit everything in one transaction."""
        for event in self._staged_events:
            payload = {
                f.name: str(getattr(event, f.name))
                for f in dataclasses.fields(event)  # type: ignore[arg-type]
                if f.name != "occurred_at"
            }
            self._session.add(
                OutboxEventModel(
                    id=str(uuid.uuid4()),
                    event_type=type(event).__name__,
                    occurred_at=event.occurred_at,
                    payload=payload,
                    published_at=None,
                )
            )
        self._staged_events = []
        await self._session.commit()

    async def rollback(self) -> None:
        self._staged_events = []
        await self._session.rollback()
```

### infrastructure/persistence/memory/__init__.py
```
```

### infrastructure/persistence/memory/memory.py
```
"""InMemory persistence adapters for unit tests."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell_ddd.domain.entities.template_graph import TemplateGraph
from shell_ddd.domain.entities.template_graph_node import TemplateGraphNode
from shell_ddd.domain.value_objects.envelope_status import EnvelopeStatus
from shell_ddd.domain.value_objects.mode import Mode
from shell_ddd.domain.value_objects.ids import (
    EnvelopeId,
    GraphId,
    MessageId,
    NodeId,
    NodeResultId,
    PromptId,
    RagChunkId,
    RagDocumentId,
    RunnerConfigId,
    SessionId,
    TaskId,
    WorkflowId, TemplateGraphId, TemplateGraphNodeId,
)

if TYPE_CHECKING:
    from shell_ddd.domain.entities.envelope import Envelope
    from shell_ddd.domain.entities.graph import Graph
    from shell_ddd.domain.entities.node_result import NodeResult
    from shell_ddd.domain.entities.prompt import Prompt
    from shell_ddd.domain.entities.rag_document import RagChunk, RagDocument
    from shell_ddd.domain.entities.runner_config import RunnerConfig
    from shell_ddd.domain.entities.session import Message, Session
    from shell_ddd.domain.entities.task import Task
    from shell_ddd.domain.entities.workflow import Workflow
    from shell_ddd.domain.events.events import DomainEvent
    from shell_ddd.domain.value_objects.task_name import TaskName

import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Repository fakes
# ---------------------------------------------------------------------------


class InMemoryTaskRepository:
    def __init__(self) -> None:
        self._store: dict[str, Task] = {}

    async def get_by_id(self, task_id: TaskId) -> Task | None:
        return self._store.get(task_id.value)

    async def get_by_name(self, name: TaskName) -> Task | None:
        for t in self._store.values():
            if t.name == name:
                return t
        return None

    async def get_current_by_name(self, name: TaskName) -> Task | None:
        for t in self._store.values():
            if t.name == name and t.is_current:
                return t
        return None

    async def save(self, task: Task) -> None:
        self._store[task.id.value] = task

    async def list_current(self) -> list[Task]:
        return [t for t in self._store.values() if t.is_current]


class InMemoryGraphRepository:
    def __init__(self) -> None:
        self._store: dict[str, "Graph"] = {}

    async def get_by_id(self, graph_id: GraphId) -> "Graph | None":
        return self._store.get(graph_id.value)

    async def get_by_task_id(self, task_id: TaskId) -> "Graph | None":
        for g in self._store.values():
            if g.task_id == task_id:
                return g
        return None

    async def save(self, graph: "Graph") -> None:
        self._store[graph.id.value] = graph


class InMemoryWorkflowRepository:
    """In-memory ``WorkflowRepository`` with optimistic concurrency control.

    Mirrors :class:`SqlWorkflowRepository` semantics so unit tests behave the
    same way as integration tests: ``save`` bumps ``Workflow.version`` and
    raises :class:`WorkflowConcurrentlyModified` if the persisted snapshot was
    written to by another caller. The persisted version is tracked
    independently of the in-memory aggregate to simulate the database row.
    """

    def __init__(self) -> None:
        self._store: dict[str, Workflow] = {}
        self._persisted_versions: dict[str, int] = {}

    async def get_by_id(self, workflow_id: WorkflowId) -> Workflow | None:
        return self._store.get(workflow_id.value)

    async def save(self, workflow: Workflow) -> None:
        from shell_ddd.domain.exceptions import WorkflowConcurrentlyModified

        existing_version = self._persisted_versions.get(workflow.id.value)
        if existing_version is None:
            workflow.version = max(workflow.version, 0) + 1
            self._store[workflow.id.value] = workflow
            self._persisted_versions[workflow.id.value] = workflow.version
            return

        if existing_version != workflow.version:
            raise WorkflowConcurrentlyModified(workflow.id.value)

        workflow.version = workflow.version + 1
        self._store[workflow.id.value] = workflow
        self._persisted_versions[workflow.id.value] = workflow.version


class InMemoryEnvelopeRepository:
    def __init__(self) -> None:
        self._store: dict[str, Envelope] = {}

    async def get_by_id(self, envelope_id: EnvelopeId) -> Envelope | None:
        return self._store.get(envelope_id.value)

    async def save(self, envelope: Envelope) -> None:
        self._store[envelope.id.value] = envelope

    async def list_by_workflow(self, workflow_id: WorkflowId, limit: int | None = None, offset: int = 0) -> list[Envelope]:
        results = [e for e in self._store.values() if e.workflow_id == workflow_id]
        results = results[offset:]
        if limit is not None:
            results = results[:limit]
        return results

    async def list_pending(self, workflow_id: WorkflowId, limit: int | None = None, offset: int = 0) -> list[Envelope]:
        results = [
            e
            for e in self._store.values()
            if e.workflow_id == workflow_id and e.status == EnvelopeStatus.PENDING
        ]
        results = results[offset:]
        if limit is not None:
            results = results[:limit]
        return results


class InMemoryEnvelopeArchive:
    def __init__(self) -> None:
        self._store: dict[str, Envelope] = {}

    async def archive(self, envelope: Envelope) -> str:
        uri = f"memory://archive/{envelope.id.value}"
        self._store[uri] = envelope
        return uri

    async def get(self, archive_uri: str) -> Envelope | None:
        return self._store.get(archive_uri)


class InMemoryPromptRepository:
    def __init__(self) -> None:
        self._store: dict[str, Prompt] = {}

    async def get_by_id(self, prompt_id: PromptId) -> Prompt | None:
        return self._store.get(prompt_id.value)

    async def get_current_by_name(self, name: str) -> Prompt | None:
        for p in self._store.values():
            if p.name == name and p.is_current:
                return p
        return None

    async def save(self, prompt: Prompt) -> None:
        self._store[prompt.id.value] = prompt


class InMemoryRunnerConfigRepository:
    def __init__(self) -> None:
        self._store: dict[str, RunnerConfig] = {}

    async def get_by_id(self, config_id: RunnerConfigId) -> RunnerConfig | None:
        return self._store.get(config_id.value)

    async def get_by_package(self, package_name: str) -> RunnerConfig | None:
        for c in self._store.values():
            if c.package_name == package_name:
                return c
        return None

    async def save(self, config: RunnerConfig) -> None:
        self._store[config.id.value] = config


class InMemoryRagDocumentRepository:
    def __init__(self) -> None:
        self._store: dict[str, RagDocument] = {}

    async def save(self, document: RagDocument) -> None:
        self._store[document.id.value] = document

    async def get_by_id(self, doc_id: RagDocumentId) -> RagDocument | None:
        return self._store.get(doc_id.value)

    async def search_similar(
            self,
            query_embedding: bytes,
            top_k: int = 5,
            domain: str | None = None,
    ) -> list[RagChunk]:
        import struct
        from shell_ddd.domain.services.rag_index_service import cosine_similarity

        dim = len(query_embedding) // 4
        query_vec = list(struct.unpack(f"{dim}f", query_embedding))
        scored: list[tuple[float, RagChunk]] = []
        for doc in self._store.values():
            if domain and doc.domain != domain:
                continue
            for chunk in doc.chunks:
                chunk_vec = list(
                    struct.unpack(f"{len(chunk.embedding) // 4}f", chunk.embedding)
                )
                score = cosine_similarity(query_vec, chunk_vec)
                scored.append((score, chunk))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [c for _, c in scored[:top_k]]


class InMemorySessionRepository:
    def __init__(self) -> None:
        self._store: dict[str, Session] = {}
        self._messages: dict[str, list[Message]] = {}

    async def save(self, session: Session) -> None:
        self._store[session.id.value] = session
        # persist messages accumulated on the entity
        existing = self._messages.get(session.id.value, [])
        existing_ids = {m.id.value for m in existing}
        for msg in session.messages:
            if msg.id.value not in existing_ids:
                existing.append(msg)
        self._messages[session.id.value] = existing

    async def get_by_id(self, session_id: SessionId) -> Session | None:
        return self._store.get(session_id.value)

    async def get_messages(self, session_id: SessionId) -> list[Message]:
        return list(self._messages.get(session_id.value, []))


# ---------------------------------------------------------------------------
# UnitOfWork fake
# ---------------------------------------------------------------------------


class InMemoryUnitOfWork:
    def __init__(self) -> None:
        self.tasks = InMemoryTaskRepository()
        self.graphs = InMemoryGraphRepository()
        self.workflows = InMemoryWorkflowRepository()
        self.envelopes = InMemoryEnvelopeRepository()
        self.prompts = InMemoryPromptRepository()
        self.runner_configs = InMemoryRunnerConfigRepository()
        self.envelope_archive = InMemoryEnvelopeArchive()
        self.rag_documents = InMemoryRagDocumentRepository()
        self.sessions = InMemorySessionRepository()
        self.template_graphs = InMemoryTemplateGraphRepository()
        # 🔥 SEED
        self.template_graphs._store["base_planner"] = TemplateGraph(
            id=TemplateGraphId("base-planner-id"),
            name="base_planner",
            purpose="default_planning",
            nodes=[
                TemplateGraphNode(
                    id=TemplateGraphNodeId("base-planner-node-1"),
                    position=0,
                    mode=Mode("agent"),
                    role="agent",
                    node_type="agent",
                ),
            ],
        )

        self._committed = False
        self._staged_events: list[DomainEvent] = []

    # ------------------------------------------------------------------
    # Outbox staging — mirrors SqlAlchemyUnitOfWork interface
    # ------------------------------------------------------------------

    def stage_events(self, events: list[DomainEvent]) -> None:
        self._staged_events.extend(events)

    @property
    def events(self) -> list[DomainEvent]:
        return list(self._staged_events)

    async def commit(self) -> None:
        self._committed = True

    async def rollback(self) -> None:
        self._staged_events = []

    async def __aenter__(self) -> InMemoryUnitOfWork:
        self._committed = False
        self._staged_events = []
        return self

    async def __aexit__(self, *args: object) -> None:
        pass


# ---------------------------------------------------------------------------
# Port fakes (Clock, IdGenerator, EventPublisher)
# ---------------------------------------------------------------------------


class FakeClock:
    def __init__(self, fixed: datetime | None = None) -> None:
        self._time = fixed or datetime(2024, 1, 1, tzinfo=UTC)

    def now(self) -> datetime:
        return self._time


class FakeIdGenerator:
    def __init__(self) -> None:
        self._counter = 0

    def _next(self) -> str:
        self._counter += 1
        return f"00000000-0000-0000-0000-{self._counter:012d}"

    def new_task_id(self) -> TaskId:
        return TaskId(self._next())

    def new_workflow_id(self) -> WorkflowId:
        return WorkflowId(self._next())

    def new_envelope_id(self) -> EnvelopeId:
        return EnvelopeId(self._next())

    def new_prompt_id(self) -> PromptId:
        return PromptId(self._next())

    def new_node_result_id(self) -> NodeResultId:
        return NodeResultId(self._next())

    def new_runner_config_id(self) -> RunnerConfigId:
        return RunnerConfigId(self._next())

    def new_rag_document_id(self) -> RagDocumentId:
        return RagDocumentId(self._next())

    def new_rag_chunk_id(self) -> RagChunkId:
        return RagChunkId(self._next())

    def new_session_id(self) -> SessionId:
        return SessionId(self._next())

    def new_message_id(self) -> MessageId:
        return MessageId(self._next())

    def new_template_graph_id(self) -> TemplateGraphId:
        return TemplateGraphId(self._next())

    def new_template_graph_node_id(self) -> TemplateGraphNodeId:
        return TemplateGraphNodeId(self._next())

    def new_graph_id(self) -> GraphId:
        return GraphId(self._next())

    def new_node_id(self) -> NodeId:
        return NodeId(self._next())


class FakeEventPublisher:
    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    async def publish(self, events: list[DomainEvent]) -> None:
        self.published.extend(events)


class FakeLogger:
    """No-op implementation of the Logger port for use in unit tests."""

    def debug(self, msg: str, **kw: object) -> None:
        pass

    def info(self, msg: str, **kw: object) -> None:
        pass

    def warning(self, msg: str, **kw: object) -> None:
        pass

    def error(self, msg: str, **kw: object) -> None:
        pass


class FakeTaskLoader:
    def __init__(self, md: str = "# Task") -> None:
        self._md = md

    async def load(self, md_path: str) -> str:
        return self._md


# ---------------------------------------------------------------------------
# Fake NodeProcessRunner / NodeWorkspace (for unit tests and bootstrap stub)
# ---------------------------------------------------------------------------


class FakeNodeProcessRunner:
    """Fake runner returning configurable ExecutionResult."""

    def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0) -> None:
        self._stdout = stdout
        self._stderr = stderr
        self._returncode = returncode
        self.calls: list[dict[str, object]] = []

    async def run(self, manifest: object, workspace_path: str, env: dict | None = None) -> object:
        from shell_ddd.domain.value_objects.execution_result import ExecutionResult

        self.calls.append({"manifest": manifest, "workspace_path": workspace_path})
        return ExecutionResult(
            stdout=self._stdout,
            stderr=self._stderr,
            returncode=self._returncode,
        )


class FakeNodeWorkspace:
    """Fake workspace that performs no filesystem operations."""

    async def prepare(self, node_id: str, work_dir: str) -> str:
        return f"/fake/workspace/{node_id}"

    async def cleanup(self, workspace_path: str) -> None:
        pass


from shell_ddd.application.dto.dto import (
    EnvelopeDto, NodeResultDto, PromptDto, RagChunkDto,
    RunnerConfigDto, SessionDto, TaskDto, WorkflowDto,
    NodeStateDto, MessageDto
)


class InMemoryQueryServices:
    """Implementacja portów odczytu dla testów jednostkowych.
    Czyta dane bezpośrednio z magazynów InMemoryUnitOfWork i mapuje je na DTO.
    """

    def __init__(self, uow: InMemoryUnitOfWork) -> None:
        self._uow = uow

    async def get_task_by_name(self, name: str) -> TaskDto | None:
        # Przeszukujemy magazyn zadań w repozytorium in-memory
        task = next(
            (t for t in self._uow.tasks._store.values() if t.name.value == name),
            None,
        )
        if not task:
            return None
        graph = await self._uow.graphs.get_by_task_id(task.id)
        graph_nodes = []
        if graph is not None:
            from shell_ddd.application.dto.dto import GraphNodeDto
            graph_nodes = [
                GraphNodeDto(
                    id=n.id.value,
                    position=n.position,
                    node_dir=n.node_dir,
                    mode=n.mode.value,
                    role=n.role,
                    node_type=n.node_type,
                    model=n.model,
                    command=n.command,
                )
                for n in graph.nodes
            ]
        return TaskDto(
            id=task.id.value,
            name=task.name.value,
            version=task.version.value,
            hash=task.hash.value,
            is_current=task.is_current,
            created_at=task.created_at,
            body=task.body.value,
            graph_nodes=graph_nodes,
        )

    async def get_current_task(self, name: str) -> TaskDto | None:
        return await self.get_task_by_name(name)

    async def get_workflow(self, workflow_id: str) -> WorkflowDto | None:

        workflow = self._uow.workflows._store.get(workflow_id)
        if not workflow:
            return None
        return WorkflowDto(
            id=str(workflow.id),
            task_name=workflow.task_name,
            status=workflow.status.value,
            created_at=workflow.created_at,
            node_states={
                str(node_id): NodeStateDto(
                    node_id=str(s.node_id),
                    status=s.status.value,
                    step=s.step,
                    updated_at=s.updated_at
                )
                for node_id, s in workflow.node_states.items()
            }
        )

    async def get_envelopes_by_workflow(
            self, workflow_id: str, pending_only: bool = False
    ) -> list[EnvelopeDto]:
        envelopes = [
            e for e in self._uow.envelopes._store.values()
            if str(e.workflow_id) == workflow_id
        ]
        if pending_only:
            envelopes = [e for e in envelopes if e.status.value == "pending"]

        return [
            EnvelopeDto(
                id=str(e.id), workflow_id=str(e.workflow_id),
                destination_node=e.destination_node, status=e.status.value,
                payload=e.payload
            ) for e in envelopes
        ]

    async def get_node_result(self, node_id: str, workflow_id: str) -> NodeResultDto | None:
        wf = await self._uow.workflows.get_by_id(WorkflowId(workflow_id))
        if wf is None:
            return None
        res = wf.node_results.get(node_id)
        if not res:
            return None
        return NodeResultDto(
            id=str(res.id),
            node_id=res.node_id,
            workflow_id=str(res.workflow_id),
            status=res.status.value,
            stdout=res.stdout,
            stderr=res.stderr,
            artifact_uri=res.artifact_uri,
            created_at=res.created_at,
        )

    async def get_prompt(self, name: str) -> PromptDto | None:
        prompt = next((p for p in self._uow.prompts._store.values() if p.name == name and p.is_current), None)
        if not prompt:
            return None
        return PromptDto(
            id=str(prompt.id),
            name=prompt.name,
            version=prompt.version,
            hash=prompt.hash,
            body=prompt.body,
            is_current=prompt.is_current,
            created_at=prompt.created_at)

    async def get_runner_config(self, package_name: str) -> RunnerConfigDto | None:
        c = self._uow.runner_configs._store.get(package_name)
        if not c:
            return None
        return RunnerConfigDto(package_name=c.package_name, version=c.version, config=c.config)

    async def get_session_history(self, session_id: str) -> SessionDto | None:
        session = self._uow.sessions._store.get(session_id)

        if session is None:
            return None

        return SessionDto(
            id=session.id.value,
            goal=session.goal,
            status=session.status,
            opened_at=session.opened_at,
            closed_at=session.closed_at,
            messages=[
                MessageDto(
                    id=message.id.value,
                    session_id=message.session_id.value,
                    correlation_id=message.correlation_id.value,
                    sender=message.sender,
                    receiver=message.receiver,
                    payload=message.payload,
                    created_at=message.created_at,
                )
                for message in session.messages
            ],
        )

    async def search_similar(
            self, query_embedding: bytes, top_k: int = 5, domain: str | None = None
    ) -> list[RagChunkDto]:
        # Prosta implementacja dla testów
        chunks = list(self._uow.rag_documents._store.values())
        return [
            RagChunkDto(
                chunk_id=f"chunk-{i}",
                document_id="doc-1",
                chunk_index=i,
                chunk_text="test content",
                source_uri="file://test.md",
                title="Test Doc",
                domain=domain or "default",
                score=1.0
            ) for i in range(min(top_k, len(chunks)))
        ]


class InMemoryTemplateGraphRepository:
    def __init__(self) -> None:
        self._store: dict[str, TemplateGraph] = {}

    async def get_template_graph_by_name(self, name: str) -> TemplateGraph | None:
        for g in self._store.values():
            if g.name == name:
                return g
        return None

    async def get_by_id(self, id_: TemplateGraphId) -> TemplateGraph | None:
        return self._store.get(id_.value)

    async def save(self, graph: TemplateGraph) -> None:
        self._store[graph.id.value] = graph


class InMemoryTemplateGraphNodeRepository:
    def __init__(self) -> None:
        self._store: dict[str, TemplateGraphNode] = {}

    async def get_by_id(self, node_id: TemplateGraphNodeId) -> TemplateGraphNode | None:
        return self._store.get(node_id.value)

    async def save(self, node: TemplateGraphNode) -> None:
        self._store[node.id.value] = node
```

### infrastructure/persistence/migrations/__init__.py
```
"""Alembic migration helpers."""
from __future__ import annotations
```

### infrastructure/persistence/migrations/mongo/__init__.py
```
```

### infrastructure/persistence/migrations/sql/__init__.py
```
"""Alembic env.py for async SQLAlchemy migrations."""
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from shell_ddd.infrastructure.persistence.sql.models import Base

# Alembic Config object
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)  # type: ignore[arg-type]

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection)  -> None:  # type: ignore[no-untyped-def]
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    url = config.get_main_option("sqlalchemy.url")
    connectable = create_async_engine(url)
    async with connectable.connect() as conn:
        await conn.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### infrastructure/persistence/migrations/sql/env.py
```
"""Alembic env.py for async SQLAlchemy migrations (SQLite + PostgreSQL)."""
from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from shell_ddd.infrastructure.persistence.sql.models import Base

# Alembic Config object
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)  # type: ignore[arg-type]

target_metadata = Base.metadata


def _get_url() -> str:
    # Allow override via env var (used in CI/docker)
    return os.environ.get("SHELL_DDD_DATABASE_URL") or config.get_main_option("sqlalchemy.url") or ""


def run_migrations_offline() -> None:
    url = _get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: object) -> None:  # type: ignore[no-untyped-def]
    context.configure(
        connection=connection,  # type: ignore[arg-type]
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    url = _get_url()
    connectable = create_async_engine(url, echo=False, future=True)
    async with connectable.connect() as conn:
        await conn.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### infrastructure/persistence/migrations/sql/versions/001_initial.py
```
"""Initial migration — creates all shell_ddd tables.

Revision ID: 001
Revises: 
Create Date: 2026-06-04
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "task",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("hash", sa.String(64), nullable=False),
        sa.Column("task_text", sa.Text, nullable=False, server_default=""),
        sa.Column("template_graph_id", sa.String(36), nullable=False),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_task_name", "task", ["name"])

    op.create_table(
        "graph",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "task_id",
            sa.String(36),
            sa.ForeignKey("task.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("raw_dict", sa.JSON, nullable=False, server_default="{}"),
    )
    op.create_index("ix_graph_task_id", "graph", ["task_id"])

    op.create_table(
        "graph_node",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "graph_id",
            sa.String(36),
            sa.ForeignKey("graph.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
        sa.Column("node_dir", sa.String(512), nullable=False, server_default=""),
        sa.Column("mode", sa.String(32), nullable=False),
        sa.Column("role", sa.String(128), nullable=False, server_default=""),
        sa.Column("node_type", sa.String(64), nullable=False, server_default=""),
        sa.Column("model", sa.String(128), nullable=False, server_default=""),
        sa.Column("command", sa.Text, nullable=False, server_default=""),
        sa.Column("timeout", sa.Integer, nullable=False, server_default="0"),
        sa.Column("retries", sa.Integer, nullable=False, server_default="0"),
        sa.Column("log_level", sa.String(16), nullable=False, server_default="INFO"),
        sa.Column("max_step", sa.Integer, nullable=False, server_default="0"),
        sa.Column("no_ask_user", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("autopilot", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("task_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("source_dir", sa.String(512), nullable=False, server_default=""),
        sa.Column("work_dir", sa.String(512), nullable=False, server_default=""),
        sa.Column("status_initial", sa.String(64), nullable=False, server_default=""),
        sa.Column("extra", sa.JSON, nullable=False, server_default="{}"),
    )
    op.create_index("ix_graph_node_graph_id", "graph_node", ["graph_id"])

    op.create_table(
        "workflow",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("task_name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="idle"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_workflow_task_name", "workflow", ["task_name"])

    op.create_table(
        "node_state",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "workflow_id",
            sa.String(36),
            sa.ForeignKey("workflow.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("node_id", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="idle"),
        sa.Column("step", sa.Integer, nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_node_state_workflow_id", "node_state", ["workflow_id"])

    op.create_table(
        "envelope",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workflow_id", sa.String(36), nullable=False),
        sa.Column("parent_id", sa.String(36), nullable=True),
        sa.Column("correlation_id", sa.String(36), nullable=False, server_default=""),
        sa.Column("sender_node_id", sa.String(255), nullable=False),
        sa.Column("receiver_node_id", sa.String(255), nullable=False),
        sa.Column("source_role", sa.String(128), nullable=False, server_default=""),
        sa.Column("target_role", sa.String(128), nullable=False, server_default=""),
        sa.Column("sequence_id", sa.Integer, nullable=False, server_default="0"),
        sa.Column("step", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("stage", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("artifact_uri", sa.String(1024), nullable=False, server_default=""),
        sa.Column("archive_uri", sa.String(1024), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_envelope_workflow_id", "envelope", ["workflow_id"])

    op.create_table(
        "envelope_event",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "envelope_id",
            sa.String(36),
            sa.ForeignKey("envelope.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_envelope_event_envelope_id", "envelope_event", ["envelope_id"])

    op.create_table(
        "node_result",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("node_id", sa.String(255), nullable=False),
        sa.Column("workflow_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("stdout", sa.Text, nullable=False, server_default=""),
        sa.Column("stderr", sa.Text, nullable=False, server_default=""),
        sa.Column("artifact_uri", sa.String(1024), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_node_result_node_id", "node_result", ["node_id"])
    op.create_index("ix_node_result_workflow_id", "node_result", ["workflow_id"])

    op.create_table(
        "prompt",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("hash", sa.String(64), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("source_uri", sa.String(1024), nullable=False, server_default=""),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_prompt_name", "prompt", ["name"])

    op.create_table(
        "runner_config",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("package_name", sa.String(255), nullable=False),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("hash", sa.String(64), nullable=False),
        sa.Column("body", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_runner_config_package_name", "runner_config", ["package_name"])

    # Envelope archive (optional — used by FileSystemEnvelopeArchive but kept for SQL completeness)
    op.create_table(
        "envelope_archive",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("envelope_id", sa.String(36), nullable=False),
        sa.Column("workflow_id", sa.String(36), nullable=False),
        sa.Column("archive_uri", sa.String(1024), nullable=False, server_default=""),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_envelope_archive_workflow_id", "envelope_archive", ["workflow_id"])
    op.create_index("ix_envelope_archive_envelope_id", "envelope_archive", ["envelope_id"])

    # Tabela template_graph
    op.create_table(
        "template_graph",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(36), nullable=False),
        sa.Column("purpose", sa.String(36), nullable=False),
    )

    # Tabela template_graph_node
    op.create_table(
        "template_graph_node",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("template_graph_id", sa.String(36), sa.ForeignKey("template_graph.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("mode", sa.String(32), nullable=False),
        sa.Column("role", sa.String(128), nullable=False),
        sa.Column("node_type", sa.String(64), nullable=False),
        sa.Column("model", sa.String(128), nullable=True),
        sa.Column("command", sa.Text, nullable=False),
        sa.Column("timeout", sa.Integer, nullable=False),
        sa.Column("retries", sa.Integer, nullable=False),
        sa.Column("log_level", sa.String(16), nullable=False),
        sa.Column("max_step", sa.Integer, nullable=True),
        sa.Column("no_ask_user", sa.Boolean, nullable=True),
        sa.Column("autopilot", sa.Boolean, nullable=True),
        sa.Column("status_initial", sa.String(64), nullable=False),
        sa.Column("extra", sa.JSON, nullable=True),
        sa.Column("script", sa.Text, nullable=True),
        sa.Column("script_type", sa.String(16), nullable=True),
    )

    # Indeks dla klucza obcego (zgodnie z wzorcem ix_envelope_workflow_id)
    op.create_index("ix_template_graph_node_graph_id", "template_graph_node", ["template_graph_id"])


def downgrade() -> None:
    op.drop_table("envelope_archive")
    op.drop_table("runner_config")
    op.drop_table("prompt")
    op.drop_table("node_result")
    op.drop_table("envelope_event")
    op.drop_table("envelope")
    op.drop_table("node_state")
    op.drop_table("workflow")
    op.drop_table("graph_node")
    op.drop_table("graph")
    op.drop_table("task")
    op.drop_table("template_graph")
    op.drop_table("template_graph_node")
```

### infrastructure/persistence/migrations/sql/versions/002_memory_rag.py
```
"""Faza 9 — adds RAG and session tables.

Revision ID: 002
Revises: 001
Create Date: 2026-06-05
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rag_document",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_uri", sa.String(1024), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("domain", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_rag_document_source_uri", "rag_document", ["source_uri"])
    op.create_index("ix_rag_document_domain", "rag_document", ["domain"])

    op.create_table(
        "rag_chunk",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "document_id",
            sa.String(36),
            sa.ForeignKey("rag_document.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer, nullable=False, server_default="0"),
        sa.Column("chunk_text", sa.Text, nullable=False),
        sa.Column("embedding", sa.LargeBinary, nullable=False),
        sa.Column("embedding_model", sa.String(128), nullable=False),
    )
    op.create_index("ix_rag_chunk_document_id", "rag_chunk", ["document_id"])

    op.create_table(
        "session",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("goal", sa.Text, nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="open"),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "message",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(36),
            sa.ForeignKey("session.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sender", sa.String(255), nullable=False),
        sa.Column("receiver", sa.String(255), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_message_session_id", "message", ["session_id"])


def downgrade() -> None:
    op.drop_table("message")
    op.drop_table("session")
    op.drop_table("rag_chunk")
    op.drop_table("rag_document")
```

### infrastructure/persistence/migrations/sql/versions/003_audit_event.py
```
"""Faza 11 — adds audit_event table.

Revision ID: 003
Revises: 002
Create Date: 2026-06-04
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_event",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
    )
    op.create_index("ix_audit_event_type", "audit_event", ["event_type"])
    op.create_index("ix_audit_event_occurred_at", "audit_event", ["occurred_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_event_occurred_at", table_name="audit_event")
    op.drop_index("ix_audit_event_type", table_name="audit_event")
    op.drop_table("audit_event")
```

### infrastructure/persistence/migrations/sql/versions/004_outbox.py
```
"""Faza 12 — adds outbox_event table.

Revision ID: 004
Revises: 003
Create Date: 2026-06-04
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "outbox_event",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_outbox_event_type", "outbox_event", ["event_type"])
    op.create_index("ix_outbox_event_published_at", "outbox_event", ["published_at"])


def downgrade() -> None:
    op.drop_index("ix_outbox_event_published_at", table_name="outbox_event")
    op.drop_index("ix_outbox_event_type", table_name="outbox_event")
    op.drop_table("outbox_event")
```

### infrastructure/persistence/migrations/sql/versions/005_split_task_graph.py
```
"""Phase 13 — split Task / Graph aggregates.

Revision ID: 005
Revises: 004
Create Date: 2026-06-15

* Drop ``task.template_graph_id``
* Rename ``task.task_text`` -> ``task.body``
* Add ``graph.template_graph_id``
* Make ``graph.task_id`` UNIQUE (1:1 with Task)
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("task") as batch:
        batch.drop_column("template_graph_id")
        batch.alter_column(
            "task_text",
            new_column_name="body",
            existing_type=sa.Text(),
            existing_nullable=False,
            existing_server_default="",
        )

    with op.batch_alter_table("graph") as batch:
        batch.add_column(
            sa.Column(
                "template_graph_id",
                sa.String(36),
                nullable=False,
                server_default="",
            )
        )
        batch.create_unique_constraint("uq_graph_task_id", ["task_id"])


def downgrade() -> None:
    with op.batch_alter_table("graph") as batch:
        batch.drop_constraint("uq_graph_task_id", type_="unique")
        batch.drop_column("template_graph_id")

    with op.batch_alter_table("task") as batch:
        batch.alter_column(
            "body",
            new_column_name="task_text",
            existing_type=sa.Text(),
            existing_nullable=False,
            existing_server_default="",
        )
        batch.add_column(
            sa.Column(
                "template_graph_id",
                sa.String(36),
                nullable=False,
                server_default="",
            )
        )
```

### infrastructure/persistence/migrations/sql/versions/006_workflow_cursor.py
```
"""Phase 14 — workflow cursor + execution context + optimistic locking.

Revision ID: 006
Revises: 005
Create Date: 2026-06-11

* Add ``workflow.current_node_id`` (nullable, indexed) — execution cursor.
* Add ``workflow.work_dir`` — captured execution context.
* Add ``workflow.correlation_id`` — captured execution context.
* Add ``workflow.version`` — optimistic concurrency token (CAS).
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("workflow") as batch:
        batch.add_column(
            sa.Column("current_node_id", sa.String(255), nullable=True, server_default=None)
        )
        batch.add_column(
            sa.Column(
                "work_dir",
                sa.String(1024),
                nullable=False,
                server_default="",
            )
        )
        batch.add_column(
            sa.Column(
                "correlation_id",
                sa.String(64),
                nullable=False,
                server_default="",
            )
        )
        batch.add_column(
            sa.Column(
                "version",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
        batch.create_index(
            "ix_workflow_current_node_id",
            ["current_node_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("workflow") as batch:
        batch.drop_index("ix_workflow_current_node_id")
        batch.drop_column("version")
        batch.drop_column("correlation_id")
        batch.drop_column("work_dir")
        batch.drop_column("current_node_id")
```

### infrastructure/persistence/migrations/sql/versions/__init__.py
```
# alembic versions package
```

### infrastructure/persistence/mongo/__init__.py
```
```

### infrastructure/persistence/mongo/documents/__init__.py
```
```

### infrastructure/persistence/mongo/mappers/__init__.py
```
```

### infrastructure/persistence/mongo/repositories/__init__.py
```
```

### infrastructure/persistence/sql/__init__.py
```
"""SQL persistence — session factory and UnitOfWork."""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from shell_ddd.infrastructure.persistence.sql.models import TemplateGraphModel


def build_session_factory(url: str) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory for the given database URL.

    Supports both SQLite (sqlite+aiosqlite://...) and
    PostgreSQL (postgresql+asyncpg://...).
    """
    engine = create_async_engine(
        url,
        echo=False,
        future=True,
        # SQLite-specific: allow same connection across threads (needed by aiosqlite)
        connect_args={"check_same_thread": False} if "sqlite" in url else {},
    )
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def create_all_tables(url: str) -> None:
    """Create all tables (dev/test helper — production uses alembic)."""
    from shell_ddd.infrastructure.persistence.sql.models import Base

    engine = create_async_engine(url, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


async def get_session(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """Async generator yielding a single AsyncSession (for use with Depends)."""
    async with session_factory() as session:
        yield session


async def seed_base_data(url: str) -> None:
    engine = create_async_engine(url, echo=False, future=True)

    async with engine.begin() as conn:
        await conn.run_sync(_seed_sync)

    await engine.dispose()


def _seed_sync(sync_conn) -> None:
    from sqlalchemy.orm import Session
    from sqlalchemy import select
    from shell_ddd.infrastructure.persistence.sql.models import TemplateGraphModel, TemplateGraphNodeModel

    session = Session(sync_conn)

    template = session.execute(
        select(TemplateGraphModel).where(
            TemplateGraphModel.name == "base_planner"
        )
    ).scalar_one_or_none()

    if template is None:
        template = TemplateGraphModel(
            id="base-planner-id",
            name="base_planner",
            purpose="default_planning",
        )
        session.add(template)
        session.flush()

    node_exists = session.execute(
        select(TemplateGraphNodeModel).where(
            TemplateGraphNodeModel.template_graph_id == template.id
        )
    ).scalar_one_or_none()

    if node_exists is None:
        session.add(
            TemplateGraphNodeModel(
                id="base-planner-node-1",
                template_graph_id=template.id,
                position=0,
                mode="agent",
                role="agent",
                node_type="agent",
                model="",
                command="",
                timeout=0,
                retries=0,
                log_level="INFO",
                max_step=None,
                no_ask_user=False,
                autopilot=False,
                status_initial="",
                extra={},
                script="",
                script_type="",
            )
        )

    session.commit()
```

### infrastructure/persistence/sql/mappers/__init__.py
```
"""SQL ORM model <-> domain entity mappers."""
from __future__ import annotations

from datetime import datetime, timezone

from shell_ddd.domain.entities.envelope import Envelope, EnvelopeEvent
from shell_ddd.domain.entities.graph import Graph
from shell_ddd.domain.entities.graph_node import GraphNode
from shell_ddd.domain.entities.node_result import NodeResult
from shell_ddd.domain.entities.prompt import Prompt
from shell_ddd.domain.entities.runner_config import RunnerConfig
from shell_ddd.domain.entities.task import Task
from shell_ddd.domain.entities.template_graph import TemplateGraph
from shell_ddd.domain.entities.template_graph_node import TemplateGraphNode
from shell_ddd.domain.entities.workflow import NodeState, Workflow
from shell_ddd.domain.value_objects.envelope_status import EnvelopeStage, EnvelopeStatus
from shell_ddd.domain.value_objects.hash import Hash
from shell_ddd.domain.value_objects.ids import (
    EnvelopeEventId,
    EnvelopeId,
    GraphId,
    NodeId,
    NodeResultId,
    NodeStateId,
    PromptId,
    RunnerConfigId,
    TaskId,
    WorkflowId, TemplateGraphNodeId, TemplateGraphId,
)
from shell_ddd.domain.value_objects.mode import Mode
from shell_ddd.domain.value_objects.status import Status
from shell_ddd.domain.value_objects.task_body import TaskBody
from shell_ddd.domain.value_objects.task_name import TaskName
from shell_ddd.domain.value_objects.version import Version
from shell_ddd.infrastructure.persistence.sql.models import (
    EnvelopeEventModel,
    EnvelopeModel,
    GraphModel,
    GraphNodeModel,
    NodeResultModel,
    NodeStateModel,
    PromptModel,
    RunnerConfigModel,
    TaskModel,
    WorkflowModel, TemplateGraphModel, TemplateGraphNodeModel,
)


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------


def task_model_to_entity(m: TaskModel) -> Task:
    return Task(
        id=TaskId(m.id),
        name=TaskName(m.name),
        version=Version(m.version),
        hash=Hash(m.hash),
        body=TaskBody(m.body),
        is_current=m.is_current,
        created_at=_ensure_utc(m.created_at),
    )


def task_entity_to_model(task: Task) -> TaskModel:
    return TaskModel(
        id=task.id.value,
        name=task.name.value,
        version=task.version.value,
        hash=task.hash.value,
        body=task.body.value,
        is_current=task.is_current,
        created_at=task.created_at,
    )


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------


def graph_model_to_entity(m: GraphModel) -> Graph:
    nodes = [
        GraphNode(
            id=NodeId(n.id),
            position=n.position,
            node_dir=n.node_dir,
            mode=Mode(n.mode),
            role=n.role,
            node_type=n.node_type,
            model=n.model,
            command=n.command,
            timeout=n.timeout,
            retries=n.retries,
            log_level=n.log_level,
            max_step=n.max_step,
            no_ask_user=n.no_ask_user,
            autopilot=n.autopilot,
            task_name=n.task_name,
            source_dir=n.source_dir,
            work_dir=n.work_dir,
            status_initial=n.status_initial,
            extra=dict(n.extra),
        )
        for n in m.nodes
    ]
    return Graph(
        id=GraphId(m.id),
        task_id=TaskId(m.task_id),
        template_graph_id=TemplateGraphId(m.template_graph_id),
        raw_dict=dict(m.raw_dict),
        nodes=nodes,
    )


def graph_entity_to_model(graph: Graph) -> GraphModel:
    m = GraphModel(
        id=graph.id.value,
        task_id=graph.task_id.value,
        template_graph_id=str(graph.template_graph_id),
        raw_dict=dict(graph.raw_dict),
    )
    m.nodes = [
        GraphNodeModel(
            id=n.id.value,
            graph_id=graph.id.value,
            position=n.position,
            node_dir=n.node_dir,
            mode=n.mode.value,
            role=n.role,
            node_type=n.node_type,
            model=n.model,
            command=n.command,
            timeout=n.timeout,
            retries=n.retries,
            log_level=n.log_level,
            max_step=n.max_step,
            no_ask_user=n.no_ask_user,
            autopilot=n.autopilot,
            task_name=n.task_name,
            source_dir=n.source_dir,
            work_dir=n.work_dir,
            status_initial=n.status_initial,
            extra=n.extra,
        )
        for n in graph.nodes
    ]
    return m


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------


def workflow_model_to_entity(m: WorkflowModel) -> Workflow:
    states = {
        ns.node_id: NodeState(
            id=NodeStateId(ns.id),
            node_id=NodeId(ns.node_id),
            status=Status(ns.status),
            step=ns.step,
            updated_at=_ensure_utc(ns.updated_at),
        )
        for ns in m.node_states
    }
    results = {
        nr.node_id: node_result_model_to_entity(nr)
        for nr in m.node_results
    }
    from shell_ddd.domain.value_objects.workflow_cursor import WorkflowCursor
    from shell_ddd.domain.value_objects.workflow_execution_context import (
        WorkflowExecutionContext,
    )

    cursor = (
        WorkflowCursor.at(NodeId(m.current_node_id))
        if m.current_node_id
        else WorkflowCursor.empty()
    )
    context = WorkflowExecutionContext(
        work_dir=m.work_dir or "",
        correlation_id=m.correlation_id or "",
    )
    return Workflow(
        id=WorkflowId(m.id),
        task_name=m.task_name,
        status=Status(m.status),
        created_at=_ensure_utc(m.created_at),
        cursor=cursor,
        execution_context=context,
        version=m.version,
        node_states=states,
        node_results=results,
    )


def workflow_entity_to_model(w: Workflow) -> WorkflowModel:
    m = WorkflowModel(
        id=w.id.value,
        task_name=w.task_name,
        status=w.status.value,
        current_node_id=w.cursor.current_node_id.value if w.cursor.current_node_id else None,
        work_dir=w.execution_context.work_dir,
        correlation_id=w.execution_context.correlation_id,
        version=w.version,
        created_at=w.created_at,
    )
    m.node_states = [
        NodeStateModel(
            id=ns.id.value,
            workflow_id=w.id.value,
            node_id=ns.node_id.value,
            status=ns.status.value,
            step=ns.step,
            updated_at=ns.updated_at,
        )
        for ns in w.node_states.values()
    ]
    m.node_results = [
        node_result_entity_to_model(nr)
        for nr in w.node_results.values()
    ]
    return m


# ---------------------------------------------------------------------------
# Envelope
# ---------------------------------------------------------------------------


def envelope_model_to_entity(m: EnvelopeModel) -> Envelope:
    evts = [
        EnvelopeEvent(
            id=EnvelopeEventId(e.id),
            kind=e.kind,
            payload=dict(e.payload),
            created_at=_ensure_utc(e.created_at),
        )
        for e in m.events
    ]
    return Envelope(
        id=EnvelopeId(m.id),
        workflow_id=WorkflowId(m.workflow_id),
        parent_id=EnvelopeId(m.parent_id) if m.parent_id else None,
        correlation_id=m.correlation_id,
        sender_node_id=NodeId(m.sender_node_id),
        receiver_node_id=NodeId(m.receiver_node_id),
        source_role=m.source_role,
        target_role=m.target_role,
        sequence_id=m.sequence_id,
        step=m.step,
        status=EnvelopeStatus(m.status),
        stage=EnvelopeStage(m.stage),
        payload=dict(m.payload),
        artifact_uri=m.artifact_uri,
        archive_uri=m.archive_uri,
        created_at=_ensure_utc(m.created_at),
        updated_at=_ensure_utc(m.updated_at),
        events=evts,
    )


def envelope_entity_to_model(e: Envelope) -> EnvelopeModel:
    m = EnvelopeModel(
        id=e.id.value,
        workflow_id=e.workflow_id.value,
        parent_id=e.parent_id.value if e.parent_id else None,
        correlation_id=e.correlation_id,
        sender_node_id=e.sender_node_id.value,
        receiver_node_id=e.receiver_node_id.value,
        source_role=e.source_role,
        target_role=e.target_role,
        sequence_id=e.sequence_id,
        step=e.step,
        status=e.status.value,
        stage=e.stage.value,
        payload=e.payload,
        artifact_uri=e.artifact_uri,
        archive_uri=e.archive_uri,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )
    m.events = [
        EnvelopeEventModel(
            id=ev.id.value,
            envelope_id=e.id.value,
            kind=ev.kind,
            payload=ev.payload,
            created_at=ev.created_at,
        )
        for ev in e.events
    ]
    return m


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------


def prompt_model_to_entity(m: PromptModel) -> Prompt:
    return Prompt(
        id=PromptId(m.id),
        name=m.name,
        version=m.version,
        hash=Hash(m.hash),
        body=m.body,
        source_uri=m.source_uri,
        is_current=m.is_current,
        created_at=_ensure_utc(m.created_at),
    )


def prompt_entity_to_model(p: Prompt) -> PromptModel:
    return PromptModel(
        id=p.id.value,
        name=p.name,
        version=p.version,
        hash=p.hash.value,
        body=p.body,
        source_uri=p.source_uri,
        is_current=p.is_current,
        created_at=p.created_at,
    )


# ---------------------------------------------------------------------------
# NodeResult
# ---------------------------------------------------------------------------


def node_result_model_to_entity(m: NodeResultModel) -> NodeResult:
    return NodeResult(
        id=NodeResultId(m.id),
        node_id=NodeId(m.node_id),
        workflow_id=WorkflowId(m.workflow_id),
        status=Status(m.status),
        stdout=m.stdout,
        stderr=m.stderr,
        artifact_uri=m.artifact_uri,
        created_at=_ensure_utc(m.created_at),
    )


def node_result_entity_to_model(r: NodeResult) -> NodeResultModel:
    return NodeResultModel(
        id=r.id.value,
        node_id=r.node_id.value,
        workflow_id=r.workflow_id.value,
        status=r.status.value,
        stdout=r.stdout,
        stderr=r.stderr,
        artifact_uri=r.artifact_uri,
        created_at=r.created_at,
    )


# ---------------------------------------------------------------------------
# RunnerConfig
# ---------------------------------------------------------------------------


def runner_config_model_to_entity(m: RunnerConfigModel) -> RunnerConfig:
    return RunnerConfig(
        id=RunnerConfigId(m.id),
        package_name=m.package_name,
        kind=m.kind,
        hash=Hash(m.hash),
        body=dict(m.body),
        created_at=_ensure_utc(m.created_at),
    )


def runner_config_entity_to_model(c: RunnerConfig) -> RunnerConfigModel:
    return RunnerConfigModel(
        id=c.id.value,
        package_name=c.package_name,
        kind=c.kind,
        hash=c.hash.value,
        body=c.body,
        created_at=c.created_at,
    )


# ---------------------------------------------------------------------------
# TemplateGraph
# ---------------------------------------------------------------------------


def template_graph_model_to_entity(
        m: TemplateGraphModel,
) -> TemplateGraph:
    return TemplateGraph(
        id=TemplateGraphId(m.id),
        name=m.name,
        purpose=m.purpose,
        nodes=[
            template_graph_node_model_to_entity(node)
            for node in m.nodes
        ],
    )


def template_graph_entity_to_model(
        graph: TemplateGraph,
) -> TemplateGraphModel:
    m = TemplateGraphModel(
        id=graph.id,
        name=graph.name,
        purpose=graph.purpose,
    )
    m.nodes = [
        template_graph_node_entity_to_model(
            node,
            graph.id,
        )
        for node in graph.nodes
    ]
    return m


def template_graph_node_model_to_entity(
        m: TemplateGraphNodeModel,
) -> TemplateGraphNode:
    return TemplateGraphNode(
        id=TemplateGraphNodeId(m.id),
        position=m.position,
        mode=Mode(m.mode),
        role=m.role,
        node_type=m.node_type,
        model=m.model or "",
        command=m.command,
        timeout=m.timeout,
        retries=m.retries,
        log_level=m.log_level,
        max_step=m.max_step,
        no_ask_user=bool(m.no_ask_user),
        autopilot=bool(m.autopilot),
        status_initial=m.status_initial,
        extra=dict(m.extra or {}),
        script=m.script or "",
        script_type=m.script_type or "",
    )


def template_graph_node_entity_to_model(
        node: TemplateGraphNode,
        template_graph_id: str,
) -> TemplateGraphNodeModel:
    return TemplateGraphNodeModel(
        id=node.id.value,
        template_graph_id=template_graph_id,
        position=node.position,
        mode=node.mode.value,
        role=node.role,
        node_type=node.node_type,
        model=node.model,
        command=node.command,
        timeout=node.timeout,
        retries=node.retries,
        log_level=node.log_level,
        max_step=node.max_step,
        no_ask_user=node.no_ask_user,
        autopilot=node.autopilot,
        status_initial=node.status_initial,
        extra=node.extra,
        script=node.script,
        script_type=node.script_type,
    )
```
