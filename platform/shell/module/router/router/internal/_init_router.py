from __future__ import annotations

from typing import TYPE_CHECKING

from shell.module.router.router_base.router_base import RouterBase

if TYPE_CHECKING:
    from shell.module.router.router.router import Router


def _init_router(router: 'Router') -> None:
    router.router_base_.init_router_base()
