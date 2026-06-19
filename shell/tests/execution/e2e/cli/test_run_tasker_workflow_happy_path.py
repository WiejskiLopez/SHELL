from __future__ import annotations

from shell.application.platform.commands.commands import RunTaskerWorkflowCommand
from shell.application.platform.queries.queries import GetWorkflowQuery
from shell.application.platform.query_handlers.query_handlers import GetWorkflowHandler
from shell.domain.execution.events import (
    GraphNodeExecutionCompletedEvent,
    WorkflowCompletedEvent,
    WorkflowFailedEvent,
)
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,
    FakeIdGenerator,
    InMemoryQueryServices,
    InMemoryUnitOfWork
)

from shell.tests.conftest import _make_task_with_graph_execution, _run_tasker_full


class TestRunTaskerWorkflowHappyPath:
    async def test_all_nodes_complete_successfully(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        queries: InMemoryQueryServices,
    ) -> None:
        task_execution, _ = _make_task_with_graph_execution(
            uow, "happy-path-task", ["agent", "tool"], clock.now()
        )
        cmd = RunTaskerWorkflowCommand(
            task_execution_id=task_execution.id.value, work_dir="/fake/work/dir"
        )
        events = await _run_tasker_full(uow, clock, id_gen, cmd)

        assert any(isinstance(e, GraphNodeExecutionCompletedEvent) for e in events)
        assert any(isinstance(e, WorkflowCompletedEvent) for e in events)
        assert not any(isinstance(e, WorkflowFailedEvent) for e in events)

        workflows = list(uow.workflows._store.values())  # type: ignore[attr-defined]
        assert len(workflows) == 1

        get_wf = GetWorkflowHandler(queries)
        dto = await get_wf.handle(GetWorkflowQuery(workflows[0].id.value))
        assert dto is not None
        assert dto.status == "done"

    async def test_single_node_workflow(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
    ) -> None:
        task_execution, _ = _make_task_with_graph_execution(
            uow, "single-node-task", ["agent"], clock.now()
        )
        cmd = RunTaskerWorkflowCommand(
            task_execution_id=task_execution.id.value, work_dir="/fake/work/dir"
        )
        events = await _run_tasker_full(uow, clock, id_gen, cmd)

        assert any(isinstance(e, WorkflowCompletedEvent) for e in events)
        workflows = list(uow.workflows._store.values())  # type: ignore[attr-defined]
        assert workflows[0].status.value == "done"
