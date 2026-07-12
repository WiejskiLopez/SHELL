---
name: midware-pipeline
description: Wzorzec Middleware/Pipeline dla handlerów w CQRS — dekoratory handlerów dla cross-cutting concerns: logowanie, monitoring, autoryzacja, transakcyjność, retry, walidacja. Używaj gdy dodajesz przekrojowe zachowanie do handlerów bez modyfikacji ich kodu.
---

# Middleware / Pipeline w Enterprise DDD

## 1. Lokalizacja

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

## 2. Podsumowanie — Checklista

Implementując middleware/pipeline:
- [ ] Middleware nie modyfikuje handlera — otacza go
- [ ] Kolejność middleware ma znaczenie (np. logowanie przed walidacją)
- [ ] Middleware testowane w isolation
- [ ] Brak zależności między middleware (niezależne)
