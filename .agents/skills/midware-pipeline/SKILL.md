---
name: midware-pipeline
description: Wzorzec Middleware/Pipeline dla handlerów w CQRS — dekoratory handlerów dla cross-cutting concerns: logowanie, monitoring, autoryzacja, transakcyjność, retry, walidacja. Używaj gdy dodajesz przekrojowe zachowanie do handlerów bez modyfikacji ich kodu.
---

# Middleware / Pipeline w Enterprise DDD

## 1. Koncepcja — Dekorowanie Handlerów

Middleware (Pipeline) to warstwa która otacza handler, dodając przekrojowe zachowanie bez modyfikacji samego handlera.

```python
# Handler — czysta logika aplikacyjna
class CreateExecutionHandler:
    async def handle(self, cmd: CreateExecutionCommand) -> None:
        async with self.uow:
            graph = await self.graph_repo.get(GraphId(cmd.graph_id))
            execution = self.factory.create_from_graph(graph)
            await self.repo.add(execution)
            self.uow.stage_events(execution.pull_events())

# Middleware — dodaje logowanie bez modyfikacji handlera
class LoggingMiddleware(CommandMiddleware):
    async def handle(self, cmd: Command, next: HandlerFunc) -> Any:
        logger.info("Handling command: %s", cmd.__class__.__name__)
        start = time.monotonic()
        try:
            result = await next(cmd)
            elapsed = time.monotonic() - start
            logger.info("Command %s completed in %.3fs", cmd.__class__.__name__, elapsed)
            return result
        except Exception as e:
            elapsed = time.monotonic() - start
            logger.error("Command %s failed after %.3fs: %s", cmd.__class__.__name__, elapsed, e)
            raise
```

## 2. Pipeline — Łańcuch Middleware

Pipeline łączy middleware w łańcuch — każdy middleware wywołuje następny.

```python
# shell/infrastructure/platform/pipeline/pipeline.py
from __future__ import annotations

from typing import Any, Callable, Protocol

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from shell.application.platform.commands import Command

HandlerFunc = Callable[[Command], Awaitable[Any]]


class CommandMiddleware(Protocol):
    async def handle(self, cmd: Command, next: HandlerFunc) -> Any: ...


class CommandPipeline:
    """Łańcuch middleware dla komend."""

    def __init__(self, handler: HandlerFunc, middlewares: list[CommandMiddleware]) -> None:
        self._handler = handler
        self._middlewares = middlewares

    async def execute(self, cmd: Command) -> Any:
        chain = self._build_chain()
        return await chain(cmd)

    def _build_chain(self) -> HandlerFunc:
        chain = self._handler
        for middleware in reversed(self._middlewares):
            next_handler = chain
            current = middleware
            chain = lambda cmd, m=current, n=next_handler: m.handle(cmd, n)
        return chain
```

## 3. Gotowe Middleware

### LoggingMiddleware

```python
class LoggingMiddleware:
    async def handle(self, cmd: Command, next: HandlerFunc) -> Any:
        logger.debug(">> %s %s", cmd.__class__.__name__, cmd)
        try:
            result = await next(cmd)
            logger.debug("<< %s OK", cmd.__class__.__name__)
            return result
        except Exception:
            logger.debug("<< %s FAIL", cmd.__class__.__name__)
            raise
```

### TransactionMiddleware (UoW)

```python
class TransactionMiddleware:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def handle(self, cmd: Command, next: HandlerFunc) -> Any:
        async with self._uow_factory() as uow:
            cmd._uow = uow  # Wstrzyknięcie UoW do handlera
            try:
                result = await next(cmd)
                await uow.commit()
                return result
            except Exception:
                await uow.rollback()
                raise
```

### AuthorizationMiddleware

```python
class AuthorizationMiddleware:
    def __init__(self, auth_service: AuthorizationService) -> None:
        self._auth_service = auth_service

    async def handle(self, cmd: Command, next: HandlerFunc) -> Any:
        user_id = getattr(cmd, "user_id", None)
        if user_id:
            self._auth_service.assert_authorized(user_id, cmd.__class__.__name__)
        return await next(cmd)
```

### ValidationMiddleware

```python
class ValidationMiddleware:
    async def handle(self, cmd: Command, next: HandlerFunc) -> Any:
        validator = getattr(cmd, "validate", None)
        if validator:
            errors = validator()
            if errors:
                raise CommandValidationError(errors)
        return await next(cmd)
```

### RetryMiddleware

```python
class RetryMiddleware:
    def __init__(self, policy: RetryPolicy = RetryPolicy()) -> None:
        self._policy = policy

    async def handle(self, cmd: Command, next: HandlerFunc) -> Any:
        last_error = None
        for attempt in range(self._policy.max_retries + 1):
            try:
                return await next(cmd)
            except TransientError as e:
                last_error = e
                if attempt < self._policy.max_retries:
                    delay = self._policy.get_delay(attempt)
                    await asyncio.sleep(delay)
                else:
                    raise
        raise last_error  # type: ignore[misc]
```

## 4. Konfiguracja Pipeline

Pipeline konfigurowany w Composition Root.

```python
# shell/bootstrap/modules/execution_module.py
class ExecutionModule:
    @staticmethod
    def register(container: Container) -> None:
        # Handler
        container.register(CreateExecutionHandler, scope=Scope.transient)

        # Middleware (kolejność ma znaczenie!)
        middlewares = [
            LoggingMiddleware(),
            ValidationMiddleware(),
            AuthorizationMiddleware(container.resolve(AuthorizationService)),
            TransactionMiddleware(container.resolve(UnitOfWork)),
        ]

        # Pipeline
        container.register(
            CommandPipeline,
            instance=CommandPipeline(
                handler=lambda cmd: container.resolve(CreateExecutionHandler).handle(cmd),
                middlewares=middlewares,
            ),
        )
```

## 5. Pipeline dla Query

Osobny pipeline dla query — inne middleware (brak transakcji, caching).

```python
class QueryPipeline:
    def __init__(self, handler: HandlerFunc, middlewares: list[QueryMiddleware]) -> None:
        ...

class CachingMiddleware:
    async def handle(self, query: Query, next: HandlerFunc) -> Any:
        cache_key = f"{query.__class__.__name__}:{hash(query)}"
        cached = await self._cache.get(cache_key)
        if cached:
            return cached
        result = await next(query)
        await self._cache.set(cache_key, result, ttl=60)
        return result
```

## 6. Lokalizacja

```
shell/infrastructure/platform/pipeline/
├── pipeline.py              # Pipeline + Middleware Protocol
├── logging_middleware.py
├── validation_middleware.py
├── authorization_middleware.py
├── transaction_middleware.py
├── retry_middleware.py
└── caching_middleware.py
```

## 7. Podsumowanie — Checklista

Implementując middleware/pipeline:
- [ ] Middleware nie modyfikuje handlera — otacza go
- [ ] Kolejność middleware ma znaczenie (np. logowanie przed walidacją)
- [ ] Pipeline konfigurowany w Composition Root
- [ ] Osobny pipeline dla command i query
- [ ] Middleware testowane w isolation
- [ ] Brak zależności między middleware (niezależne)
- [ ] Middleware może przerywać łańcuch (np. błąd autoryzacji)
- [ ] Monitoring dodany przez middleware (metryki, tracing)
