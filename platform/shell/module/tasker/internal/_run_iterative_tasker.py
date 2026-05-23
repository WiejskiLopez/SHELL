from __future__ import annotations

from shell.structure.graph.graph.internal._persist_node_status import _persist_node_status
from shell.structure.graph.graph_node.internal._run_sub_node import _run_sub_node
from shell.status.status import Status
from shell.module.tasker.internal._seed_task_to_first_node import _seed_task_to_first_node
from shell.module.tasker.internal._find_node_with_input import _find_node_with_input
from shell.module.tasker.internal._has_router_work import _has_router_work
from shell.module.tasker.internal._has_own_output import _has_own_output
from shell.module.tasker.internal._has_own_input import _has_own_input
from shell.module.tasker.internal._move_router_output_to_own import _move_router_output_to_own
from shell.module.tasker.internal._init_task_md import _init_task_md
from shell.module.tasker.internal._init_task_yaml import _init_task_yaml
from shell.module.tasker.internal._init_task_prompts import _init_task_prompts
from shell.utils.path.path import Path
from shell.constants.constants import DOT_NODE, DIR_INPUT, DIR_OUTPUT, DIR_TASK

_MAX_ITERATIONS = 200


def _run_iterative_tasker(tasker) -> Status:
    app = tasker._app
    task_dir = (app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK).resolve()

    if _has_own_output(app):
        app.app_trace_.record_info('tasker._run_iterative_tasker', 'own output not empty — skipping execution')
        return Status.SUCCESS

    if not _has_own_input(app):
        app.app_trace_.record_info('tasker._run_iterative_tasker', 'own input empty — skipping execution')
        return Status.SUCCESS


    iteration = 0
    # _seed_task_to_first_node(tasker, task_dir)

    _own_node_dir = app.app_node_.node_.node_dir_ / DOT_NODE
    _input_dir = _own_node_dir / DIR_INPUT
    _output_dir = _own_node_dir / DIR_OUTPUT
    _input_files = Path.iterdir(_input_dir) if Path.exists(_input_dir) else []
    _output_files = Path.iterdir(_output_dir) if Path.exists(_output_dir) else []
    app.app_trace_.record_info('tasker._run_iterative_tasker', f'input dir: {_input_dir} files: {[f.name for f in _input_files]}')
    app.app_trace_.record_info('tasker._run_iterative_tasker', f'output dir: {_output_dir} files: {[f.name for f in _output_files]}')

    while True:
        if iteration >= _MAX_ITERATIONS:
            raise RuntimeError(f"tasker stalled after {_MAX_ITERATIONS} iterations without reaching DONE")
        iteration += 1

        sub_nodes = tasker.graph_.sub_nodes_
        non_router_nodes = [pn for pn in sub_nodes if pn.mode_ != 'router']
        router_nodes = [pn for pn in sub_nodes if pn.mode_ == 'router']

        if _move_router_output_to_own(tasker, app):
            return Status.DONE

        node_with_input = _find_node_with_input(non_router_nodes)
        if node_with_input is not None:
            app.app_trace_.record_info('tasker._run_iterative_tasker', f"agent input found — running {node_with_input.node_name_}")
            status = _run_sub_node(node_with_input, task_dir, app)
            _persist_node_status(node_with_input, app)
            if status == Status.ERROR:
                return Status.ERROR
            continue

        if router_nodes:
            router_node = router_nodes[0]
            if _has_router_work(non_router_nodes, router_node):
                app.app_trace_.record_info('tasker._run_iterative_tasker', f"router work found — running {router_node.node_name_}")
                status = _run_sub_node(router_node, task_dir, app)
                _persist_node_status(router_node, app)
                if status == Status.ERROR:
                    return Status.ERROR
                if status == Status.DONE:
                    _move_router_output_to_own(tasker, app)
                    return Status.DONE
                continue

            if _has_own_input(app):
                app.app_trace_.record_info('tasker._run_iterative_tasker', f"own input not empty — running {router_node.node_name_}")
                status = _run_sub_node(router_node, task_dir, app)
                _persist_node_status(router_node, app)
                if status == Status.ERROR:
                    return Status.ERROR
                if status == Status.DONE:
                    _move_router_output_to_own(tasker, app)
                    return Status.DONE
                continue

            app.app_trace_.record_info('tasker._run_iterative_tasker', f"no work — flushing via {router_node.node_name_}")
            status = _run_sub_node(router_node, task_dir, app)
            _persist_node_status(router_node, app)
            if status == Status.ERROR:
                return Status.ERROR
            if status == Status.DONE:
                _move_router_output_to_own(tasker, app)
                return Status.DONE
            break

        break

    return Status.SUCCESS
