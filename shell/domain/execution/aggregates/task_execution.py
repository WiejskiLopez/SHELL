"""Task aggregate root.

Task represents a versioned, named definition of work to be performed.
After a Task is created (`task_execution.create`), it emits a ``TaskExecutionCreatedEvent`` event
that other aggregates (notably ``Graph``) react to. Task does NOT know
which graph_execution realises it — that responsibility belongs to ``Graph``.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from shell.domain.execution.events import TaskExecutionCreatedEvent
from shell.domain.execution.value_objects.task_execution_body import TaskExecutionBody
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
from shell.domain.platform.base import AggregateRoot
from shell.domain.platform.value_objects.hash import Hash
from shell.domain.platform.value_objects.version import Version

if TYPE_CHECKING:
    from shell.domain.execution.value_objects.ids import TaskExecutionId, WorkflowId


class TaskExecution(AggregateRoot["TaskExecutionId"]):
    """TaskExecution aggregate root."""

    __slots__ = (
        "_parent_task_execution_id",
        "_name",
        "_version",
        "_hash",
        "_body",
        "_is_current",
        "_created_at",
        "_work_dir",
        "_workflow_id",
    )

    _parent_task_execution_id: TaskExecutionId | None
    _name: TaskExecutionName
    _version: Version
    _hash: Hash
    _body: TaskExecutionBody
    _is_current: bool
    _created_at: datetime
    _work_dir: str
    _workflow_id: WorkflowId | None  # owning workflow (optional)

    def __init__(
        self,
        id: TaskExecutionId,
        parent_task_execution_id: TaskExecutionId | None = None,
        name: TaskExecutionName | None = None,
        version: Version | None = None,
        hash: Hash | None = None,
        body: TaskExecutionBody | None = None,
        is_current: bool = True,
        created_at: datetime | None = None,
        work_dir: str = "",
        workflow_id: WorkflowId | None = None,
    ) -> None:
        super().__init__(id)
        self._parent_task_execution_id = parent_task_execution_id
        self._name = name or TaskExecutionName("")
        self._version = version or Version.initial()
        self._hash = hash or Hash.of("")
        self._body = body or TaskExecutionBody("")
        self._is_current = is_current
        self._created_at = created_at or datetime.min
        self._work_dir = work_dir
        self._workflow_id = workflow_id

    @property
    def parent_task_execution_id(self) -> TaskExecutionId | None:
        return self._parent_task_execution_id

    @property
    def name(self) -> TaskExecutionName:
        return self._name

    @property
    def version(self) -> Version:
        return self._version

    @property
    def hash(self) -> Hash:
        return self._hash

    @property
    def body(self) -> TaskExecutionBody:
        return self._body

    @property
    def is_current(self) -> bool:
        return self._is_current

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def work_dir(self) -> str:
        return self._work_dir

    @work_dir.setter
    def work_dir(self, value: str) -> None:
        self._work_dir = value

    @property
    def workflow_id(self) -> WorkflowId | None:
        return self._workflow_id

    @classmethod
    def create(
        cls,
        *,
        id_: TaskExecutionId,
        name: TaskExecutionName,
        body: TaskExecutionBody,
        now: datetime,
        parent_task_execution_id: TaskExecutionId | None = None,
        workflow_id: WorkflowId | None = None,
    ) -> TaskExecution:
        """Factory for a brand-new Task (version 1, current). Emits TaskExecutionCreatedEvent."""
        task_execution = cls(
            id=id_,
            parent_task_execution_id=parent_task_execution_id,
            name=name,
            version=Version.initial(),
            hash=Hash.of(body.value),
            body=body,
            is_current=True,
            created_at=now,
            workflow_id=workflow_id,
        )
        task_execution.append_event(
            TaskExecutionCreatedEvent.now(task_execution_id=id_, task_execution_name=name, now=now)
        )
        return task_execution

    def supersede(self) -> None:
        """Mark this Task as no longer current (a newer version supersedes it)."""
        self._is_current = False

    def bump_version(self) -> None:
        self._version = self._version.next()

    def rename(self, new_name: TaskExecutionName) -> None:
        self._name = new_name
