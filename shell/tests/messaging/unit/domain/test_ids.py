from __future__ import annotations

import pytest

from shell.domain.execution.value_objects.ids import TaskExecutionId, WorkflowId
from shell.domain.messaging.aggregates.message.value_objects.message_id import MessageId


class TestIds:
    def test_task_execution_id_generate(self) -> None:
        t1 = TaskExecutionId.generate()
        t2 = TaskExecutionId.generate()
        assert t1 != t2
        assert len(t1.value) == 36

    def test_task_execution_id_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            TaskExecutionId("")

    def test_workflow_id_generate(self) -> None:
        w = WorkflowId.generate()
        assert w.value

    def test_message_id_generate(self) -> None:
        m = MessageId.generate()
        assert m.value
