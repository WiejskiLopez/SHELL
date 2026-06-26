"""Integration tests for optimistic locking across all versioned SQL models."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pytest
from shell.domain.platform.exceptions.concurrent_modification_error import (
    ConcurrentModificationError,
)
from shell.infrastructure.platform.persistence import SqlAlchemyUnitOfWork

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

_NOW = datetime(2024, 1, 1)


async def _test_dual_commit(
    session_factory: async_sessionmaker,
    model_class: type,
    pk: str,
    field: str,
    val_a: object,
    val_b: object,
    **kwargs: object,
) -> None:
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        inst = model_class(id=pk, **kwargs)
        uow._active_session.add(inst)
        await uow.commit()

    uow_a = SqlAlchemyUnitOfWork(session_factory)
    uow_b = SqlAlchemyUnitOfWork(session_factory)

    async with uow_a as ua, uow_b as ub:
        ma = await ua._active_session.get(model_class, pk)
        mb = await ub._active_session.get(model_class, pk)
        assert ma is not None and mb is not None
        assert ma.version == 1 and mb.version == 1

        setattr(ma, field, val_a)
        await ua.commit()

        setattr(mb, field, val_b)
        with pytest.raises(ConcurrentModificationError):
            await ub.commit()


class TestWorkflowOptimisticLocking:
    async def test_concurrent_modification_raises_error(
        self, session_factory: async_sessionmaker,
    ) -> None:
        from shell.infrastructure.execution.persistence.sql.models import WorkflowModel
        await _test_dual_commit(session_factory, WorkflowModel, "ol-wf-1",
                                "status", "completed", "aborted",
                                status="active", created_at=_NOW)


class TestTaskExecutionOptimisticLocking:
    async def test_concurrent_modification_raises_error(
        self, session_factory: async_sessionmaker,
    ) -> None:
        from shell.infrastructure.execution.persistence.sql.models import TaskExecutionModel
        await _test_dual_commit(session_factory, TaskExecutionModel, "ol-te-1",
                                "status", "in_progress", "failed",
                                status="created", name="t", work_dir="/tmp",
                                created_at=_NOW)


class TestGraphExecutionOptimisticLocking:
    async def test_concurrent_modification_raises_error(
        self, session_factory: async_sessionmaker,
    ) -> None:
        from shell.infrastructure.execution.persistence.sql.models import TaskExecutionModel, GraphExecutionModel
        uid = "ol-ge-1"
        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            te = TaskExecutionModel(id=uid + "-te", status="created", name="t",
                                     work_dir="/tmp", created_at=_NOW)
            uow._active_session.add(te)
            ge = GraphExecutionModel(id=uid, task_execution_id=uid + "-te",
                                      graph_definition_id="tpl", status="pending",
                                      state_input={}, state_output={}, depth=0,
                                      correlation_id="", tags={})
            uow._active_session.add(ge)
            await uow.commit()

        uow_a = SqlAlchemyUnitOfWork(session_factory)
        uow_b = SqlAlchemyUnitOfWork(session_factory)
        async with uow_a as ua, uow_b as ub:
            ma = await ua._active_session.get(GraphExecutionModel, uid)
            mb = await ub._active_session.get(GraphExecutionModel, uid)
            assert ma is not None and mb is not None and ma.version == 1 and mb.version == 1
            ma.status = "planning"
            await ua.commit()
            mb.status = "executing"
            with pytest.raises(ConcurrentModificationError):
                await ub.commit()


class TestGraphNodeExecutionOptimisticLocking:
    async def test_concurrent_modification_raises_error(
        self, session_factory: async_sessionmaker,
    ) -> None:
        from shell.infrastructure.execution.persistence.sql.models import (
            TaskExecutionModel, GraphExecutionModel, GraphNodeExecutionModel,
        )
        uid = "ol-gne-1"
        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            te = TaskExecutionModel(id=uid + "-te", status="created", name="t",
                                     work_dir="/tmp", created_at=_NOW)
            uow._active_session.add(te)
            ge = GraphExecutionModel(id=uid + "-ge", task_execution_id=uid + "-te",
                                      graph_definition_id="tpl", status="pending",
                                      state_input={}, state_output={}, depth=0,
                                      correlation_id="", tags={})
            uow._active_session.add(ge)
            ne = GraphNodeExecutionModel(
                id=uid, graph_execution_id=uid + "-ge", position=0, mode="agent",
                role="agent", node_type="agent", model="", command="", retries=0,
                log_level="INFO", max_step=0, no_ask_user=False, autopilot=False,
                task_execution_id=uid + "-te", source_dir="/tmp", status_initial="",
                timeout_seconds=0, max_retries=0, retry_delay_seconds=0,
            )
            uow._active_session.add(ne)
            await uow.commit()

        uow_a = SqlAlchemyUnitOfWork(session_factory)
        uow_b = SqlAlchemyUnitOfWork(session_factory)
        async with uow_a as ua, uow_b as ub:
            ma = await ua._active_session.get(GraphNodeExecutionModel, uid)
            mb = await ub._active_session.get(GraphNodeExecutionModel, uid)
            assert ma is not None and mb is not None and ma.version == 1 and mb.version == 1
            ma.log_level = "DEBUG"
            await ua.commit()
            mb.log_level = "ERROR"
            with pytest.raises(ConcurrentModificationError):
                await ub.commit()


class TestGraphNodeTransitionExecutionOptimisticLocking:
    async def test_concurrent_modification_raises_error(
        self, session_factory: async_sessionmaker,
    ) -> None:
        from shell.infrastructure.execution.persistence.sql.models import (
            TaskExecutionModel, GraphExecutionModel, GraphNodeExecutionModel,
            GraphNodeTransitionExecutionModel,
        )
        uid = "ol-gnte-1"
        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            te = TaskExecutionModel(id=uid + "-te", status="created", name="t",
                                     work_dir="/tmp", created_at=_NOW)
            uow._active_session.add(te)
            ge = GraphExecutionModel(id=uid + "-ge", task_execution_id=uid + "-te",
                                      graph_definition_id="tpl", status="pending",
                                      state_input={}, state_output={}, depth=0,
                                      correlation_id="", tags={})
            uow._active_session.add(ge)
            ne = GraphNodeExecutionModel(
                id=uid + "-ne", graph_execution_id=uid + "-ge", position=0, mode="agent",
                role="agent", node_type="agent", model="", command="", retries=0,
                log_level="INFO", max_step=0, no_ask_user=False, autopilot=False,
                task_execution_id=uid + "-te", source_dir="/tmp", status_initial="",
                timeout_seconds=0, max_retries=0, retry_delay_seconds=0,
            )
            uow._active_session.add(ne)
            tr = GraphNodeTransitionExecutionModel(
                id=uid, graph_execution_id=uid + "-ge",
                source_node_execution_id=uid + "-ne",
                target_node_execution_id=uid + "-ne",
                transition_type="SEQUENCE", priority=0, max_loop_count=0,
                retry_count=0, retry_delay_seconds=0, label="",
                created_at=_NOW, updated_at=_NOW,
            )
            uow._active_session.add(tr)
            await uow.commit()

        uow_a = SqlAlchemyUnitOfWork(session_factory)
        uow_b = SqlAlchemyUnitOfWork(session_factory)
        async with uow_a as ua, uow_b as ub:
            ma = await ua._active_session.get(GraphNodeTransitionExecutionModel, uid)
            mb = await ub._active_session.get(GraphNodeTransitionExecutionModel, uid)
            assert ma is not None and mb is not None and ma.version == 1 and mb.version == 1
            ma.priority = 1
            await ua.commit()
            mb.priority = 2
            with pytest.raises(ConcurrentModificationError):
                await ub.commit()


class TestSessionOptimisticLocking:
    async def test_concurrent_modification_raises_error(
        self, session_factory: async_sessionmaker,
    ) -> None:
        from shell.infrastructure.execution.persistence.sql.models import SessionModel
        from datetime import timezone
        await _test_dual_commit(session_factory, SessionModel, "ol-s-1",
                                "status", "closed", "paused",
                                goal="test", status="open",
                                opened_at=_NOW.replace(tzinfo=timezone.utc))


class TestEnvelopeOptimisticLocking:
    async def test_concurrent_modification_raises_error(
        self, session_factory: async_sessionmaker,
    ) -> None:
        from shell.infrastructure.execution.persistence.sql.models import EnvelopeModel
        await _test_dual_commit(
            session_factory, EnvelopeModel, "ol-e-1",
            "status", "active", "dead",
            workflow_id="w1", parent_id=None, correlation_id="c1",
            sender_graph_node_execution_id="s1", receiver_graph_node_execution_id="r1",
            source_role="agent", target_role="router",
            sequence_id=0, step=0, status="pending", stage="draft",
            payload={}, artifact_uri="", archive_uri="",
            created_at=_NOW, updated_at=_NOW,
        )


class TestGraphDefinitionOptimisticLocking:
    async def test_concurrent_modification_raises_error(
        self, session_factory: async_sessionmaker,
    ) -> None:
        from shell.infrastructure.definition.persistence.sql.models import GraphDefinitionModel
        await _test_dual_commit(session_factory, GraphDefinitionModel, "ol-gd-1",
                                "name", "v2", "v3",
                                name="v1", purpose="test")


class TestGraphNodeDefinitionOptimisticLocking:
    async def test_concurrent_modification_raises_error(
        self, session_factory: async_sessionmaker,
    ) -> None:
        from shell.infrastructure.definition.persistence.sql.models import (
            GraphDefinitionModel, GraphNodeDefinitionModel,
        )
        uid = "ol-gnd-1"
        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            gd = GraphDefinitionModel(id=uid + "-gd", name="test", purpose="test")
            uow._active_session.add(gd)
            nd = GraphNodeDefinitionModel(
                id=uid, graph_definition_id=uid + "-gd", position=0,
                mode="agent", role="agent", node_type="agent",
                model="", command="", timeout=0, retries=0,
                log_level="INFO", max_step=None, no_ask_user=None,
                autopilot=None, status_initial="", script=None, script_type=None,
            )
            uow._active_session.add(nd)
            await uow.commit()

        uow_a = SqlAlchemyUnitOfWork(session_factory)
        uow_b = SqlAlchemyUnitOfWork(session_factory)
        async with uow_a as ua, uow_b as ub:
            ma = await ua._active_session.get(GraphNodeDefinitionModel, uid)
            mb = await ub._active_session.get(GraphNodeDefinitionModel, uid)
            assert ma is not None and mb is not None and ma.version == 1 and mb.version == 1
            ma.position = 1
            await ua.commit()
            mb.position = 2
            with pytest.raises(ConcurrentModificationError):
                await ub.commit()


class TestRunnerConfigOptimisticLocking:
    async def test_concurrent_modification_raises_error(
        self, session_factory: async_sessionmaker,
    ) -> None:
        from shell.infrastructure.definition.persistence.sql.models import RunnerConfigModel
        await _test_dual_commit(session_factory, RunnerConfigModel, "ol-rc-1",
                                "package_name", "v2", "v3",
                                package_name="v1", kind="python", hash="abc",
                                body={}, created_at=_NOW)


class TestRagDocumentOptimisticLocking:
    async def test_concurrent_modification_raises_error(
        self, session_factory: async_sessionmaker,
    ) -> None:
        from shell.infrastructure.definition.persistence.sql.models import RagDocumentModel
        await _test_dual_commit(session_factory, RagDocumentModel, "ol-rd-1",
                                "source_uri", "https://v2.example.com", "https://v3.example.com",
                                source_uri="https://v1.example.com", title="V1",
                                domain="test", created_at=_NOW)


class TestSchedulerDefinitionOptimisticLocking:
    async def test_concurrent_modification_raises_error(
        self, session_factory: async_sessionmaker,
    ) -> None:
        from shell.infrastructure.scheduling.persistence.sql.models.scheduler_definition import (
            SchedulerDefinitionModel,
        )
        await _test_dual_commit(session_factory, SchedulerDefinitionModel, "ol-sd-1",
                                "name", "v2", "v3",
                                name="v1", source_context="ctx", trigger_event_type="evt",
                                trigger_filter=None, action_type="action", action_config={},
                                execution_policy=None, enabled=True,
                                created_at=_NOW, updated_at=_NOW)


class TestSchedulerJobOptimisticLocking:
    async def test_concurrent_modification_raises_error(
        self, session_factory: async_sessionmaker,
    ) -> None:
        from shell.infrastructure.scheduling.persistence.sql.models.scheduler_execution import (
            SchedulerExecutionModel,
        )
        await _test_dual_commit(session_factory, SchedulerExecutionModel, "ol-sj-1",
                                "name", "v2", "v3",
                                scheduler_definition_id="sd1", name="v1",
                                created_at=_NOW, updated_at=_NOW)
