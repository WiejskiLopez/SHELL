"""_save_archive.py
Phase — archive the node execution state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.app.app.app import App


def _save_archive(app: 'App', clock=None) -> None:
    app.app_node_.node_.node_archive_.save_archive(clock=clock)
