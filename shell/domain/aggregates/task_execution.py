"""Task aggregate root.

Task represents a versioned, named definition of work to be performed.
After a Task is created (`task_execution.create`), it emits a ``TaskExecutionCreated`` event
that other aggregates (notably ``Graph``) react to. Task does NOT know
which graph_execution realises it — that responsibility belongs to ``Graph``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.entities.base import AggregateRoot
from shell.domain.events.events import TaskExecutionCreated
from shell.domain.value_objects.hash import Hash
from shell.domain.value_objects.version import Version

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.value_objects.ids import TaskExecutionId
    from shell.domain.value_objects.task_execution_body import TaskExecutionBody
    from shell.domain.value_objects.task_execution_name import TaskExecutionName


class TaskExecution(AggregateRoot["TaskExecutionId"]):
    """TaskExecution aggregate root."""

    __slots__ = (
        "_name",
        "_version",
        "_hash",
        "_body",
        "_is_current",
        "_created_at",
    )

    _name: TaskExecutionName
    _version: Version
    _hash: Hash
    _body: TaskExecutionBody
    _is_current: bool
    _created_at: datetime

    def __init__(
        self,
        id: TaskExecutionId,
        name: TaskExecutionName,
        version: Version,
        hash: Hash,
        body: TaskExecutionBody,
        is_current: bool,
        created_at: datetime,
    ) -> None:
        super().__init__(id)
        self._name = name
        self._version = version
        self._hash = hash
        self._body = body
        self._is_current = is_current
        self._created_at = created_at

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

    @classmethod
    def create(
        cls,
        *,
        id_: TaskExecutionId,
        name: TaskExecutionName,
        body: TaskExecutionBody,
        now: datetime,
    ) -> TaskExecution:
        """Factory for a brand-new Task (version 1, current). Emits TaskExecutionCreated."""
        task_execution = cls(
            id=id_,
            name=name,
            version=Version.initial(),
            hash=Hash.of(body.value),
            body=body,
            is_current=True,
            created_at=now,
        )
        task_execution.append_event(
            TaskExecutionCreated.now(task_execution_id=id_, task_execution_name=name, now=now)
        )
        return task_execution

    def supersede(self) -> None:
        """Mark this Task as no longer current (a newer version supersedes it)."""
        self._is_current = False

    def bump_version(self) -> None:
        self._version = self._version.next()

    def rename(self, new_name: TaskExecutionName) -> None:
        self._name = new_name
