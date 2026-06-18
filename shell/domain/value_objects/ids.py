"""Typed ID value objects."""

from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TaskExecutionId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("TaskExecutionId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> TaskExecutionId:
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
class GraphNodeExecutionId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("GraphNodeExecutionId cannot be empty")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class GraphExecutionId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("GraphExecutionId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> GraphExecutionId:
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
class GraphNodeExecutionResultId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("GraphNodeExecutionResultId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> GraphNodeExecutionResultId:
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
class GraphDefinitionId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("GraphDefinitionId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> GraphDefinitionId:
        return cls(str(uuid.uuid4()))


@dataclass(frozen=True, slots=True)
class GraphNodeDefinitionId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("GraphNodeDefinitionId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> GraphNodeDefinitionId:
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
class GraphNodeExecutionStateId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("GraphNodeExecutionStateId cannot be empty")

    def __str__(self) -> str:
        return self.value

    @classmethod
    def generate(cls) -> GraphNodeExecutionStateId:
        return cls(str(uuid.uuid4()))
