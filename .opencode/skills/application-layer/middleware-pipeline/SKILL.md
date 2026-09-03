---
name: middleware-pipeline
description: "Wzorzec Middleware/Pipeline dla handlerów w CQRS — dekoratory handlerów dla cross-cutting concerns: logowanie, monitoring, autoryzacja, transakcyjność, retry, walidacja. Używaj gdy dodajesz przekrojowe zachowanie do handlerów bez modyfikacji ich kodu."
---

# Middleware / Pipeline dla handlerów CQRS

## Status implementacji w SHELL

**SHELL nie posiada obecnie pipeline'u middleware dla handlerów CQRS.** Warstwa HTTP korzysta z natywnych middleware FastAPI w `shell/platform/framework/api/middleware/` (`api_key.py`, `api_version.py`, `audit_log.py`, `correlation_id.py`, `error_handler.py`) — patrz `shell-specific/backend-api-standards`.

Niniejszy skill opisuje **wzorzec docelowy** cross-cutting concerns dla handlerów (logowanie, autoryzacja, transakcyjność, retry, walidacja, cache). Gdy pipeline dla handlerów zostanie zaimplementowany, musi przestrzegać reguł poniżej oraz struktury `pattern-standards/middleware-structure`.

## 1. Zasada

- Middleware nie modyfikuje handlera — otacza go.
- Kolejność middleware ma znaczenie (np. logowanie przed walidacją).
- Middleware może przerwać łańcuch (np. brak uprawnień).
- Middleware są testowane w izolacji i nie mają wzajemnych zależności.

## 2. Lokalizacja docelowa

```
shell/platform/infrastructure/pipeline/
├── pipeline.py              # Pipeline + Middleware Protocol
├── logging_middleware.py
├── validation_middleware.py
├── authorization_middleware.py
├── transaction_middleware.py
├── retry_middleware.py
└── caching_middleware.py
```

## 3. Checklista

Implementując middleware/pipeline:
- [ ] Middleware nie modyfikuje handlera — otacza go
- [ ] Kolejność middleware ma znaczenie (np. logowanie przed walidacją)
- [ ] Middleware testowane w isolation
- [ ] Brak zależności między middleware (niezależne)
- [ ] Pipeline konfigurowany w Composition Root
- [ ] Osobny pipeline dla command i query

## Powiązane skille

- `pattern-standards/middleware-structure` — struktura klas Middleware i Pipeline