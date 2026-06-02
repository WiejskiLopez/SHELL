"""_run_iterative_tasker.py
Tasker run loop: bus-based, DB-backed.

Owns the workflow lifecycle:
- open_workflow / close_workflow on WorkflowState
- seeds first envelope(s) from own .node/input/ (read via tasker's DbNodePort)
- iterates: router subprocess (PENDING -> ACTIVE) then dispatch ACTIVE per node
- for each receiver: writes envelope payload into receiver's input scope via DbNodePort
- spawns subprocess (FS contract for entrypoint, DB for data)
- collects responses from receiver's output scope via DbNodePort and republishes
- finalizes when bus has no active envelopes
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shell.bus.envelope.envelope_status import EnvelopeStatus
from shell.bus.envelope.envelope_stage import EnvelopeStage
from shell.constants.constants import DOT_NODE, DIR_INPUT, DIR_OUTPUT, DIR_TASK
from shell.module.tasker.internal._has_own_input import _has_own_input
from shell.module.tasker.internal._has_own_output import _has_own_output
from shell.status.status import Status
from shell.structure.graph.graph.internal._persist_node_status import _persist_node_status
from shell.structure.node.node_port.db_node_port import DbNodePort
from shell.structure.sub_node.sub_node.internal._run_sub_node import _run_sub_node
from shell.utils.path.path import Path

if TYPE_CHECKING:
    from shell.module.tasker.tasker import Tasker

_MAX_ITERATIONS = 200


def _run_iterative_tasker(tasker: 'Tasker') -> Status:
    app = tasker._app
    bus = app.bus_
    state = app.workflow_state_

    if _has_own_output(app):
        app.app_trace_.record_info('tasker._run_iterative_tasker', 'own output not empty — skipping execution')
        return Status.SUCCESS

    workflow_id = _resolve_workflow_id(tasker)
    has_db_envelopes = _has_pending_envelopes_in_db(bus, workflow_id)

    if not has_db_envelopes and not _has_own_input(app):
        app.app_trace_.record_info('tasker._run_iterative_tasker', 'own input empty and no DB envelopes — skipping execution')
        return Status.SUCCESS

    state.open_workflow(
        workflow_id,
        root_task_id=workflow_id,
        task_id=app.task_record_.task_id_,
        session_id=tasker.session_id_,
    )
    app.app_trace_.record_info('tasker._run_iterative_tasker', f'workflow opened: {workflow_id}')

    sub_nodes = tasker.graph_.sub_nodes_
    router_nodes = [n for n in sub_nodes if n.mode_ == 'router']
    non_router_nodes = [n for n in sub_nodes if n.mode_ != 'router']

    if not has_db_envelopes:
        _seed_initial_envelopes(workflow_id, bus, non_router_nodes, app)
    else:
        app.app_trace_.record_info('tasker._run_iterative_tasker', 'using pre-seeded DB envelopes — skipping file seed')

    task_dir = Path.resolve(app.app_node_.node_.node_dir_ / DOT_NODE / DIR_TASK)

    iteration = 0
    while True:
        if iteration >= _MAX_ITERATIONS:
            raise RuntimeError(f"tasker stalled after {_MAX_ITERATIONS} iterations without reaching DONE")
        iteration += 1
        app.app_trace_.record_info('tasker._run_iterative_tasker', f'iteration={iteration}')

        if router_nodes:
            router_node = router_nodes[0]
            _set_subprocess_workflow_args(router_node, workflow_id, None)
            router_status = _run_sub_node(router_node, task_dir, app)
            _persist_node_status(router_node, app, workflow_id)
            if router_status == Status.ERROR:
                state.close_workflow(workflow_id, status='FAILED')
                return Status.ERROR

        any_dispatched = False
        for receiver_node in non_router_nodes:
            envelope = bus.claim_next(workflow_id, receiver_node.node_name_)
            if envelope is None:
                continue
            any_dispatched = True
            app.app_trace_.record_info(
                'tasker._run_iterative_tasker',
                f'claimed envelope id={envelope.id_} -> node={receiver_node.node_name_}'
            )

            _materialize_envelope_to_input(envelope, receiver_node, workflow_id, app)
            _set_subprocess_workflow_args(receiver_node, workflow_id, envelope.id_)
            receiver_status = _run_sub_node(receiver_node, task_dir, app)
            _persist_node_status(receiver_node, app, workflow_id)

            if receiver_status == Status.ERROR:
                bus.mark_status(envelope.id_, EnvelopeStatus.FAILED, source='tasker')
                state.close_workflow(workflow_id, status='FAILED')
                return Status.ERROR

            _publish_response_envelopes(receiver_node, envelope, workflow_id, bus, app)
            bus.mark_status(envelope.id_, EnvelopeStatus.COMPLETED, source='tasker')
            bus.move_to_stage(envelope.id_, EnvelopeStage.HISTORY, source='tasker', reason='completed')

        if not any_dispatched and not bus.has_active(workflow_id):
            break

    state.close_workflow(workflow_id, status='COMPLETED')
    app.app_trace_.record_info('tasker._run_iterative_tasker', f'workflow completed after {iteration} iterations')

    _collect_final_outputs_to_own(tasker, workflow_id, bus, app)

    return Status.DONE


def _has_pending_envelopes_in_db(bus, workflow_id: str) -> bool:
    rows = bus.driver_.query(
        "SELECT COUNT(*) as cnt FROM envelope WHERE workflow_id = ? AND stage = 'PENDING'",
        (workflow_id,),
    )
    return bool(rows and rows[0]["cnt"] > 0)


def _resolve_workflow_id(tasker: 'Tasker') -> str:
    name = tasker._app.app_node_.node_.node_task_.task_name_
    if name:
        return name
    return tasker.task_name_


def _build_port(app, node_dir, node_name, workflow_id) -> DbNodePort:
    port = DbNodePort()
    port.init_db_node_port(app.memory_, node_dir, node_name, workflow_id)
    return port


def _seed_initial_envelopes(workflow_id, bus, non_router_nodes, app) -> None:
    own_input = app.app_node_.node_.node_dir_ / DOT_NODE / DIR_INPUT
    files = Path.iterdir(own_input) if Path.exists(own_input) else []
    target_role = non_router_nodes[0].role_ if non_router_nodes else None
    for f in files:
        body = Path.read_text(f)
        envelope_id = bus.publish_envelope(
            workflow_id=workflow_id,
            source_role='tasker',
            sender_node_id='tasker',
            target_role=target_role,
            payload={'body': body, 'filename': f.name},
            step=0,
        )
        app.app_trace_.record_info(
            'tasker._seed_initial_envelopes',
            f'seeded envelope id={envelope_id} file={f.name} target_role={target_role}'
        )


def _materialize_envelope_to_input(envelope, receiver_node, workflow_id, app) -> None:
    node_dir = receiver_node.sub_node_properties_.node_dir_
    node_name = receiver_node.node_name_
    port = _build_port(app, node_dir, node_name, workflow_id)
    input_dir = node_dir / DOT_NODE / DIR_INPUT
    port.makedirs(input_dir)
    try:
        payload = json.loads(envelope.payload_json_) if envelope.payload_json_ else {}
    except (ValueError, TypeError):
        payload = {}
    body = payload.get('body') if isinstance(payload, dict) else None
    if body is None:
        body = envelope.payload_json_ or ''
    base = (payload.get('filename') if isinstance(payload, dict) else None) or (
        f"{envelope.sequence_id_:06d}__{envelope.source_role_ or 'unknown'}__to__{envelope.target_role_ or 'any'}.md"
    )
    port.write_text(input_dir / base, body)


def _extract_target_role(body: str) -> str | None:
    first_line = body.lstrip().split('\n', 1)[0].strip()
    if first_line.upper().startswith('TARGET:'):
        return first_line[7:].strip().lower() or None
    return None


def _publish_response_envelopes(receiver_node, parent_envelope, workflow_id, bus, app) -> None:
    node_dir = receiver_node.sub_node_properties_.node_dir_
    node_name = receiver_node.node_name_
    port = _build_port(app, node_dir, node_name, workflow_id)
    output_dir = node_dir / DOT_NODE / DIR_OUTPUT
    if not port.exists(output_dir):
        return
    for f in port.list_files(output_dir):
        body = port.read_text(f)
        target_role = _extract_target_role(body)
        envelope_id = bus.publish_envelope(
            workflow_id=workflow_id,
            parent_envelope_id=parent_envelope.id_,
            source_role=receiver_node.role_,
            sender_node_id=receiver_node.node_name_,
            target_role=target_role,
            payload={'body': body, 'filename': f.name},
            step=parent_envelope.step_ + 1,
        )
        app.app_trace_.record_info(
            'tasker._publish_response_envelopes',
            f'published response id={envelope_id} from={receiver_node.node_name_} file={f.name}'
        )


def _collect_final_outputs_to_own(tasker, workflow_id, bus, app) -> None:
    own_output = app.app_node_.node_.node_dir_ / DOT_NODE / DIR_OUTPUT
    Path.mkdir(own_output)
    history = bus.get_history_for_workflow(workflow_id)
    leaves = [e for e in history if e.target_role_ is None or e.target_role_ == 'tasker']
    for envelope in leaves:
        try:
            payload = json.loads(envelope.payload_json_) if envelope.payload_json_ else {}
        except (ValueError, TypeError):
            payload = {}
        body = payload.get('body') if isinstance(payload, dict) else None
        if body is None:
            continue
        filename = (payload.get('filename') if isinstance(payload, dict) else None) or f"{envelope.sequence_id_:06d}.md"
        Path.write_text(own_output / filename, body)


def _set_subprocess_workflow_args(sub_node, workflow_id: str, envelope_id) -> None:
    cmd_list = sub_node.sub_node_command_.command_.command_
    _strip_arg(cmd_list, '--workflow-id')
    _strip_arg(cmd_list, '--envelope-id')
    cmd_list.extend(['--workflow-id', workflow_id])
    if envelope_id is not None:
        cmd_list.extend(['--envelope-id', str(envelope_id)])


def _strip_arg(cmd_list: list, flag: str) -> None:
    while flag in cmd_list:
        idx = cmd_list.index(flag)
        del cmd_list[idx:idx + 2]
