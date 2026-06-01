"""_init_app.py
Phase 1 — build and return a App from CLI args.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.app.app.internal._init_app_modules import _init_app_modules
from shell.app.app.internal._init_app_config import _init_app_config

if TYPE_CHECKING:
    from shell.app.app.app import App


def _init_app(
    cls,
    argv: list[str] | None = None,
    mode: str | None = None,
    runner_root_dir: str | None = None,
    # --- test seams (injectable overrides) ---
    *,
    make_dirs=None,
    version_info: tuple[int, ...] | None = None,
    locker=None,
) -> App:
    app = cls()
    try:
        app.cli_.init_cli(argv=argv, runner_root_dir=runner_root_dir, mode=mode)
        app.runtime_.init_runtime(version_info=version_info)
        _init_app_modules(app, mode=mode, locker=locker)
        _init_app_config(app)
    except Exception as exc:
        app.app_trace_.record_error_and_raise('app._init_app._init_app', exc)
    return app
