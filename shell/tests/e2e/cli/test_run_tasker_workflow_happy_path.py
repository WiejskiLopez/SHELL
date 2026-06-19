from __future__ import annotations

from shell.application.commands.commands import RunTaskerWorkflowCommand
from shell.application.queries.queries import GetWorkflowQuery
from shell.application.query_handlers.query_handlers import GetWorkflowHandler
from shell.domain.events.events import (
    GraphNodeExecutionCompleted,
    WorkflowCompleted,
    WorkflowFailed,
)
from shell.infrastructure.persistence.memory import (
    FakeClock,
    FakeIdGenerator,
    InMemoryQueryServices,
    InMemoryUnitOfWork,
)

from .conftest import _make_task_with_graph_execution, _run_tasker_full


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

        assert any(isinstance(e, GraphNodeExecutionCompleted) for e in events)
        assert any(isinstance(e, WorkflowCompleted) for e in events)
        assert not any(isinstance(e, WorkflowFailed) for e in events)

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

        assert any(isinstance(e, WorkflowCompleted) for e in events)
        workflows = list(uow.workflows._store.values())  # type: ignore[attr-defined]
        assert workflows[0].status.value == "done"
