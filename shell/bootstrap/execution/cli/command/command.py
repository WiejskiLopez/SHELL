from __future__ import annotations

from abc import ABC, abstractmethod
from argparse import (
    Namespace,  # noqa: TC003 — argparse.Namespace used in run() signature at runtime
)


class RunnableCommand(ABC):
    """Interfejs dla poleceń CLI (wzorzec Command)."""

    @abstractmethod
    async def run(self, args: Namespace) -> None:
        pass
