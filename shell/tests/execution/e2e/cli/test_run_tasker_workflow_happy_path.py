from __future__ import annotations

from shell.application.platform.commands import RunTaskerWorkflowCommand
from shell.application.platform.queries.queries import WorkflowGetByIdQuery
from shell.application.platform.query_handlers import WorkflowGetByIdHandler
from shell.domain.execution.events import (
    GraphNodeExecutionCompletedEvent,
    WorkflowCompletedEvent,
    WorkflowFailedEvent,
)
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,  # noqa: TC002 — FakeClock używany w sygnaturach fixture'ów pytest
    FakeIdGenerator,  # noqa: TC002 — FakeIdGenerator używany w sygnaturach fixture'ów pytest
    InMemoryQueryServices,  # noqa: TC002 — InMemoryQueryServices używany w sygnaturach fixture'ów pytest
    InMemoryUnitOfWork,  # noqa: TC002 — InMemoryUnitOfWork używany w sygnaturach fixture'ów pytest
)
from shell.tests.conftest_helpers import _make_task_with_graph_execution, _run_tasker_full


class TestRunTaskerWorkflowHappyPath:
    async def test_all_nodes_complete_successfully(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        queries: InMemoryQueryServices,
    ) -> None:
        task_execution, _ = _make_task_with_graph_execution(
            unit_of_work, "happy-path-task", ["agent", "tool"], clock.now()
        )
        command = RunTaskerWorkflowCommand(
            task_execution_id=task_execution.id.value, work_dir="/fake/work/dir"
        )
        events = await _run_tasker_full(unit_of_work, clock, id_generator, command)

        assert any(isinstance(e, GraphNodeExecutionCompletedEvent) for e in events)
        assert any(isinstance(e, WorkflowCompletedEvent) for e in events)
        assert not any(isinstance(e, WorkflowFailedEvent) for e in events)

        workflows = list(unit_of_work.workflow_repository._store.values())
        assert len(workflows) == 1

        get_wf = WorkflowGetByIdHandler(queries)
        dto = await get_wf.handle(WorkflowGetByIdQuery(workflows[0].id.value))
        assert dto is not None
        assert dto.status == "completed"

    async def test_single_node_workflow(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
    ) -> None:
        task_execution, _ = _make_task_with_graph_execution(
            unit_of_work, "single-node-task", ["agent"], clock.now()
        )
        command = RunTaskerWorkflowCommand(
            task_execution_id=task_execution.id.value, work_dir="/fake/work/dir"
        )
        events = await _run_tasker_full(unit_of_work, clock, id_generator, command)

        assert any(isinstance(e, WorkflowCompletedEvent) for e in events)
        workflows = list(unit_of_work.workflow_repository._store.values())
        assert workflows[0].status.value == "completed"
