from __future__ import annotations

from collections.abc import Callable
from typing import Any


class QueryBus:
    """Przesyła zapytania do dynamicznie rozwiązanych handlerów."""

    def __init__(self) -> None:
        self._factories: dict[type[Any], Callable[[], Any]] = {}

    def register(self, query_type: type[Any], factory: Callable[[], Any]) -> None:
        self._factories[query_type] = factory

    async def dispatch(self, query: Any) -> Any:
        factory = self._factories[type(query)]
        handler = factory()
        return await handler.handle(query)
