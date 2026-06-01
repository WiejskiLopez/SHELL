"""_finalize_app.py
Phase — release the lock and clean up after execution.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.app.app.app import App


def _finalize_app(app: 'App', rmtree=None, unlink=None) -> None:
    app.app_node_.release_node(rmtree=rmtree, unlink=unlink)
