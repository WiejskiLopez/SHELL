"""_init_worker.py
Delegate initialization to worker_properties.
"""

from __future__ import annotations


def _init_worker(worker, reader=None) -> None:
    app = worker._app

    try:
        worker.worker_properties_.init_worker_properties()
    except ValueError as exc:
        app.app_trace_.record_error_and_raise('worker._init_worker._init_worker', exc)
