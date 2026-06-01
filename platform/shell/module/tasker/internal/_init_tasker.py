from __future__ import annotations

from datetime import datetime

from shell.module.tasker.internal._import_task_to_db import _import_task_to_db


def _init_tasker(tasker, reader=None) -> None:
    record = _import_task_to_db(tasker._app)
    tasker._app.set_task_record(record)
    tasker._session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    tasker.graph_.init_graph()
