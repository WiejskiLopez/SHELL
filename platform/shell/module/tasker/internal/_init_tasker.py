from __future__ import annotations

from datetime import datetime

from shell.module.tasker.internal._import_task_to_db import _import_task_to_db


def _init_tasker(tasker, reader=None) -> None:
    tasker._task_record = _import_task_to_db(tasker._app)
    tasker._session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    tasker.graph_.init_graph()
