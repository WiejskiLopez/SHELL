#!/usr/bin/env python
"""Create event files for state aggregates."""
from pathlib import Path

for rel, name, id_type, id_module in [
    ("shell/domain/execution/aggregates/session_execution_state/events/session_execution_state_created_event.py",
     "SessionExecutionState", "SessionExecutionStateId",
     "shell.domain.execution.aggregates.session_execution_state.value_objects.session_execution_state_id"),
    ("shell/domain/execution/aggregates/task_execution_state/events/task_execution_state_created_event.py",
     "TaskExecutionState", "TaskExecutionStateId",
     "shell.domain.execution.aggregates.task_execution_state.value_objects.task_execution_state_id"),
    ("shell/domain/execution/aggregates/user_execution_state/events/user_execution_state_created_event.py",
     "UserExecutionState", "UserExecutionStateId",
     "shell.domain.execution.aggregates.user_execution_state.value_objects.user_execution_state_id"),
]:
    p = Path(rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f'''from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from {id_module} import {id_type}
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class {name}CreatedEvent(DomainEvent):
    {name.lower()}_id: {id_type}

    @classmethod
    def now(cls, {name.lower()}_id: {id_type}, now: CreatedAt) -> "{name}CreatedEvent":
        return cls(occurred_at=now, {name.lower()}_id={name.lower()}_id)
''')
    print(f"EVENT: {p}")

print("Done")
