from __future__ import annotations

import pytest

from shell.execution.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.execution.domain.execution.aggregates.workflow.value_objects.workflow_id import (
    WorkflowId,
)
from shell.messaging.domain.messaging.aggregates.message_router.value_objects.message_router_id import (
    MessageRouterId,
)


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
        m = MessageRouterId.generate()
        assert m.value
