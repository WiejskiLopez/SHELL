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
