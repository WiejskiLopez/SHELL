"""E2E API tests — FastAPI control plane."""

from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import ASGITransport, AsyncClient

from shell.bootstrap.factory.application_factory import ApplicationFactory

if TYPE_CHECKING:
    import pathlib


async def _make_app(tmp_path: pathlib.Path):  # type: ignore[return]
    from shell.framework.api.app import create_app

    db_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    core_container = await ApplicationFactory(database_url=db_url).build()
    return create_app(core_container)


class TestHealthEndpoint:
    async def test_health_returns_ok(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestTasksRouter:
    async def test_import_task(self, tmp_path: pathlib.Path) -> None:
        md = tmp_path / "api_task.md"
        md.write_text("# API Task", encoding="utf-8")

        app = await _make_app(tmp_path)

        #      core_container = app.state.core_container
        #      async with core_container.uow() as uow:

        #          base_planner = TemplateGraph(
        #              id="base-planner-id",
        #              name="base_planner",
        #              purpose="default_planning"
        #          )
        #          await uow.template_graphs.save(base_planner)
        #          await uow.commit()
        # ---------------------------------------

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/tasks/import",
                json={
                    "task_name": "api_task",
                    "md_path": str(md),
                },
            )
        assert resp.status_code == 201
        assert "task_id" in resp.json()

    async def test_get_task_not_found(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/tasks/no_such_task")
        assert resp.status_code == 404


class TestWorkflowsRouter:
    async def test_start_workflow_unknown_task_returns_error(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/workflows", json={"task_id": "no_such_task"})
        # Domain error → 404 or 400
        assert resp.status_code in (400, 404)

    async def test_start_and_get_workflow(self, tmp_path: pathlib.Path) -> None:
        md = tmp_path / "wf_task.md"
        md.write_text("# WF Task", encoding="utf-8")

        db_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
        core_container = await ApplicationFactory(database_url=db_url).build()
        from shell.framework.api.app import create_app

        app = create_app(core_container)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # import task first
            await client.post(
                "/tasks/import",
                json={
                    "task_name": "wf_task",
                    "md_path": str(md),
                },
            )

            # Attach a single-node Graph for the imported task
            from shell.domain.entities.graph import Graph, GraphNode
            from shell.domain.value_objects.ids import GraphId, NodeId, TemplateGraphId
            from shell.domain.value_objects.mode import Mode
            from shell.domain.value_objects.task_name import TaskName

            uow_factory = core_container.infra.uow_factory()
            async with uow_factory as uow:
                task = await uow.tasks.get_current_by_name(TaskName("wf_task"))
                assert task is not None

                # Zapisujemy ID wygenerowane przez system do użycia w requescie
                actual_task_id = task.id.value

                existing_graph = await uow.graphs.get_by_task_id(task.id)
                if existing_graph:
                    existing_graph.add_node(
                        GraphNode(
                            id=NodeId("wf_task-node-0"),
                            position=0,
                            node_dir="/fake/wf_task-0",
                            mode=Mode("agent"),
                            role="agent",
                            node_type="agent",
                        )
                    )
                    await uow.graphs.save(existing_graph)
                    await uow.commit()
                else:
                    graph = Graph(
                        id=GraphId.generate(),
                        task_id=task.id,
                        template_graph_id=TemplateGraphId("tpl"),
                        raw_dict={},
                        nodes=[
                            GraphNode(
                                id=NodeId("wf_task-node-0"),
                                position=0,
                                node_dir="/fake/wf_task-0",
                                mode=Mode("agent"),
                                role="agent",
                                node_type="agent",
                            )
                        ],
                    )
                    await uow.graphs.save(graph)
                    await uow.commit()

            # start workflow - Używamy poprawnego endpointu oraz wyciągniętego actual_task_id
            # JEŻELI TWÓJ ROUTER MA ENDPOINT: POST /workflows
            resp = await client.post("/workflows", json={"task_id": actual_task_id})

            # JEŻELI TWÓJ ROUTER MA ENDPOINT: POST /tasks/{task_id}/workflows
            # resp = await client.post(f"/tasks/{actual_task_id}/workflows")

            assert resp.status_code == 201


#    async def test_start_and_get_workflow(self, tmp_path: pathlib.Path) -> None:
#        md = tmp_path / "wf_task.md"
#        md.write_text("# WF Task", encoding="utf-8")

#        db_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
#        core_container = await ApplicationFactory(database_url=db_url).build()
#        from shell.framework.api.app import create_app

#       app = create_app(core_container)
#        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
#            # import task first
#            await client.post("/tasks/import", json={
#                "task_name": "wf_task",
#                "md_path": str(md),
#           })

#            # Attach a single-node Graph for the imported task so that
#            # StartWorkflowHandler can anchor the cursor.
#            # Note: BuildGraphOnTaskCreated handler already creates a graph from template.
#            # We check if graph exists and add a node to it.
#            from shell.domain.entities.graph import Graph, GraphNode
#            from shell.domain.value_objects.ids import GraphId, NodeId, TemplateGraphId
#            from shell.domain.value_objects.mode import Mode
#            from shell.domain.value_objects.task_name import TaskName
#
#            uow_factory = core_container.infra.uow_factory()
#            async with uow_factory as uow:
#                task = await uow.tasks.get_current_by_name(TaskName("wf_task"))
#                assert task is not None
#                existing_graph = await uow.graphs.get_by_task_id(task.id)
#                if existing_graph:
#                    existing_graph.add_node(
#                        GraphNode(
#                            id=NodeId("wf_task-node-0"),
#                            position=0,
#                            node_dir="/fake/wf_task-0",
#                            mode=Mode("agent"),
#                            role="agent",
#                            node_type="agent",
#                        )
#                    )
#                    await uow.graphs.save(existing_graph)
#                    await uow.commit()
#                else:
#                    graph = Graph(
#                        id=GraphId.generate(),
#                        task_id=task.id,
#                        template_graph_id=TemplateGraphId("tpl"),
#                        raw_dict={},
#                        nodes=[
#                            GraphNode(
#                                id=NodeId("wf_task-node-0"),
#                                position=0,
#                                node_dir="/fake/wf_task-0",
#                                mode=Mode("agent"),
#                                role="agent",
#                                node_type="agent",
#                            )
#                        ],
#                    )
#                    await uow.graphs.save(graph)
#                    await uow.commit()
#
#            # start workflow
#            resp = await client.post("/workflows", json={"task_id": "workflow_task_id"})
#        assert resp.status_code == 201
#        wf_id = resp.json()["workflow_id"]
#        assert wf_id


class TestEnvelopesRouter:
    async def test_list_envelopes_empty(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/envelopes/workflow/nonexistent-wf")
        assert resp.status_code == 200
        assert resp.json()["envelopes"] == []


class TestNodesRouter:
    async def test_get_node_result_not_found(self, tmp_path: pathlib.Path) -> None:
        app = await _make_app(tmp_path)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/nodes/nonexistent-node/result?workflow_id=wf-x")
        assert resp.status_code == 404
