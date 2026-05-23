from shell.utils.path.path import PathType
"""_get_logger.py
Private. Responsible for one thing: providing a configured logger
that writes to a log file (configured level) and stderr (WARNING+).

Log format: timestamp | level | message
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from shell.utils.io.io import default_file_handler, default_make_dirs
from shell.logger.internal._build_log_path import _build_log_path
from shell.logger.internal._make_formatter import _make_formatter
from shell.logger.internal._resolve_level import _resolve_level


def _get_logger(app, make_dirs: Callable[[PathType], None] | None = None, make_file_handler: Callable[[PathType], logging.FileHandler] | None = None) -> logging.Logger:
    """Return an isolated logger writing to a log file and stderr.

    On first call builds and configures the logger, then caches it on the Logger facade.
    Subsequent calls return the cached instance directly.
    make_dirs:         optional callable (path: PathType) -> None (defaults to mkdir with parents).
    make_file_handler: optional callable (path: PathType) -> logging.FileHandler.
    """
    logger = app.app_trace_.logger_
    if logger.cached_logger_ is not None:
        return logger.cached_logger_

    if make_dirs is None:
        make_dirs = default_make_dirs
    if make_file_handler is None:
        make_file_handler = default_file_handler

    node_dir = app.app_node_.node_.node_dir_
    log_level: str = logger._log_level or 'INFO'
    role: str = app.app_properties_.role_ or app.cli_.cli_properties_.task_name_ or 'unknown'
    log_path = _build_log_path(node_dir, log_level, role=role)
    level_int = _resolve_level(log_level)

    make_dirs(log_path.parent)
    logging_logger = logging.getLogger(str(log_path))
    logging_logger.setLevel(level_int)
    logging_logger.propagate = False

    fmt = _make_formatter()
    fh = make_file_handler(log_path)
    fh.setLevel(level_int)
    fh.setFormatter(fmt)

    sh = logging.StreamHandler()
    sh.setLevel(logging.WARNING)
    sh.setFormatter(fmt)

    logging_logger.addHandler(fh)
    logging_logger.addHandler(sh)
    logger.cached_logger_ = logging_logger
    app.app_trace_.record_info('logger._get_logger._get_logger', f'log file {log_path}')
    return logging_logger
