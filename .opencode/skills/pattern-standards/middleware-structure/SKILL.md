---
name: middleware-structure
description: Reguły struktury Middleware i Pipeline — kolejność middleware, pipeline dla command/query, gotowe middlewares.
---

# Middleware / Pipeline Structure

> Reguły struktury klas Middleware i Pipeline w warstwie aplikacyjnej.

## Status implementacji w SHELL

Warstwa HTTP korzysta z natywnych middleware FastAPI w `shell/platform/framework/api/middleware/` (`api_key`, `api_version`, `audit_log`, `correlation_id`, `error_handler`). **Pipeline middleware dla handlerów CQRS nie jest jeszcze zaimplementowany w SHELL** — poniższe reguły definiują wzorzec docelowy, do którego ma się stosować przyszła implementacja (patrz `application-layer/middleware-pipeline`).

## Definicja

- Middleware (Pipeline) to warstwa która otacza handler, dodając przekrojowe zachowanie bez modyfikacji samego handlera.
- Pipeline łączy middleware w łańcuch — każdy middleware wywołuje następny.

## Middleware

- Sygnatura: `async handle(self, command: Command, next: HandlerFunc) -> Any`.

```python
class LoggingMiddleware:
    async def handle(self, command: Command, next: HandlerFunc) -> Any:
        logger.info('Handling %s', type(command).__name__)
        try:
            result = await next(command)
            logger.info('Handled %s successfully', type(command).__name__)
            return result
        except Exception:
            logger.exception('Failed to handle %s', type(command).__name__)
            raise
```

## Kolejność

- Kolejność middleware ma znaczenie (np. logowanie przed walidacją).
- Osobny pipeline dla command i query.

```python
# Command pipeline: Logging → Transaction → Authorization → Validation → Handler
command_pipeline = Pipeline(
    middlewares=[
        LoggingMiddleware(),
        TransactionMiddleware(unit_of_work),
        AuthorizationMiddleware(auth_service),
        ValidationMiddleware(),
    ],
)
```

## Pipeline

- Pipeline konfigurowany w Composition Root.
- Middleware opakowuje handler (dekoracyjna otoczka); logika handlera pozostaje bez zmian.
- Middleware może przerywać łańcuch (np. błąd autoryzacji).

```python
class Pipeline:
    def __init__(self, middlewares: list[Middleware]) -> None:
        self._middlewares = middlewares

    async def execute(self, command: Command, handler: Handler) -> Any:
        chain = self._build_chain(handler)
        return await chain(command)

    def _build_chain(self, handler: Handler) -> HandlerFunc:
        chain = handler.handle
        for middleware in reversed(self._middlewares):
            chain = partial(middleware.handle, next=chain)
        return chain
```

## Gotowe middlewares

- `LoggingMiddleware` — logowanie wejścia/wyjścia
- `TransactionMiddleware` — UoW (commit/rollback)
- `AuthorizationMiddleware` — sprawdzenie uprawnień
- `ValidationMiddleware` — walidacja strukturalna komendy
- `RetryMiddleware` — retry dla transient errors
- `CachingMiddleware` — cache dla query

## Izolacja

- Middleware testowane w isolation.
- Brak zależności między middleware (niezależne).

## Lokalizacja

- Docelowo: `shell/platform/infrastructure/pipeline/` (katalog wymaga utworzenia).
