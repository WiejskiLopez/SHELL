from __future__ import annotations

from abc import ABC, abstractmethod
from argparse import Namespace


class RunnableCommand(ABC):
    """Interfejs dla poleceń CLI (wzorzec Command)."""

    @abstractmethod
    async def run(self, args: Namespace) -> None:
        pass
