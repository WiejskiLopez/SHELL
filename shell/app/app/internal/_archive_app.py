from __future__ import annotations

from typing import TYPE_CHECKING

from shell.component.result.result import Result

if TYPE_CHECKING:
    from shell.app.app.app import App


def _archive_app(app: App) -> None:
    app._result = Result.from_trace(app.app_trace_, app)
    app.app_node_.node_.node_archive_.save_archive()
    app.result_.save_result()
