from __future__ import annotations

import pytest

from shell.execution_service.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.execution_service.domain.execution.aggregates.workflow.value_objects.workflow_id import (
    WorkflowId,
)
from shell.ingestion_service.domain.ingestion.aggregates.ingestion.value_objects.ingestion_id import (
    IngestionId,
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

    def test_ingestion_id_generate(self) -> None:
        m = IngestionId.generate()
        assert m.value
