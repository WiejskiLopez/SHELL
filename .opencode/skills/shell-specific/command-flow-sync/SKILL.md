---
name: command-flow-sync
description: Przepływ komendy SYNCHRONICZNEGO (lokalnego, w obrębie jednego BC) — HTTP → Controller → CommandBus → Handler → UoW → Aggregate → commit + odpowiedź. Wszystkie klasy po drodze, granice transakcji i ryzyka (brak idempotencji na API). Używaj gdy projektujesz/refaktoryzujesz lokalny endpoint komendy, handler komendy, UoW, agregat, rejestrację do CommandBus, albo analizujesz czy komenda synchroniczna może zostać zgubiona/zduplikowana.
---

# Command Flow SYNCHRONICZNY w SHELL

## Charakterystyka

- Tryb: `HTTP → Controller → CommandBus → Handler → UnitOfWork → Aggregate → commit`. Komenda jako **obiekt w pamięci**, odpowiedź wraca bezpośrednio do caller'a.
- Transakcja: **jedna lokalna** — własna sesja UoW handlera (brak session scope).
- Zasięg: ten sam proces/BC; komenda żyje jako obiekt w pamięci (poza bazą).
- Gwarancja: sync request/response. Awaria → wyjątek do API, brak trwałego stanu.

Pełny dokument: `command-flow-sync.md` (root repo).

## Klasy po kolei (przykład `POST /api/v1/projects/`)

```
create_*_app (FastAPI, app.py)                        framework/<bc>/.../api/app.py:29
  → CorrelationIdMiddleware (correlation_id)          platform/framework/api/middleware/correlation_id.py:16-39
  → AuthMiddleware (X-API-Key)
  → router.py (APIRouter) + Depends(get_core_container)  framework/<bc>/.../api/router.py:28,31-40,60-65
  → Controller.create_* (CommandBus.dispatch)         framework/<bc>/.../api/controller.py:96-100
  → CommandBus.dispatch (factory() → handler)         platform/application/bus/command_bus.py:9-21
  → Handler (koordynacja UoW/VO; logika biznesowa w domenie)    application/<bc>/.../command_handlers/create_*_handler.py
  → SqlAlchemy*UnitOfWork → SqlAlchemyUnitOfWorkBase  infrastructure/<bc>/.../unit_of_work.py:25-35
       __aenter__: scope=None → WŁASNA sesja (nie deferred)  platform/infrastructure/persistence/sql_alchemy_uow_base.py:117-129
       save(repo_type, aggregate) → aggregate.pull_events()   :111-115
       commit(): _write_staged_outbox() + session.commit()    :142-190
  → Aggregate.create() → append_event(DomainEvent)     domain/<bc>/aggregates/.../aggregate.py; platform/domain/base/aggregate_root.py:27-40
  → commit atomowy: stan agregatu + outbox_event + audit_event
  → odpowiedź (DTO) → HTTP 201/204/404
```

Rejestracja handlera: `configure_*_container(container)` w `bootstrap/<bc>/container/*.py` — `command_bus().register(CommandType, handler_factory)`. Każda komenda musi mieć handler.

## Granice odpowiedzialności

- **Framework** — router, controller, request/response DTO, middleware. Tylko przekazanie.
- **Application** — Command (frozen dataclass), Handler (koordynacja). Logika biznesowa żyje w domenie.
- **Domain** — Aggregate, DomainEvent, VO, Repository port. Guard-y i invarianty w metodach domenowych.
- **Infrastructure** — UoW, SqlRepository, `PERSISTENCE_DELIVERY_MODELS`, serializacja outboxa.
- **Bootstrap** — kontener + `configure_*_container` (rejestracje do busów), `main.py` (composition root).

## Granica transakcji

- 1 transakcja: **stan agregatu + outbox_event + audit_event** (`sql_alchemy_uow_base.py:142-190`).
- Crash przed commitem → rollback → spójnie: stan w całości albo wcale, bez cząstkowych zapisów.
- `StaleDataError` → `ConcurrentModificationError` + rollback (:155-157).

## Ryzyka ścieżki synchronicznej

1. **Brak idempotencji na API** — endpointy POST nie mają `Idempotency-Key` (router.py:60-65). Crash po commicie a przed odpowiedzią, lub retry klienta → **duplikat efektu** (np. drugi projekt). Command nie niesie stabilnego id.
2. Komenda żyje w pamięci; crash w trakcie handlera kończy działanie bez efektu — akceptowalne
   dla sync HTTP; operacje wymagające odtwarzalności przechodzą na delivery (outbox→inbox).
3. Wiele agregatów w 1 transakcji — poza repo mapą BC wymaga domain-service / wzorca unit-of-work.

**Podsumowanie:** transakcja sync jest atomowa (albo cały efekt, albo nic); wyzwaniem jest
deduplikacja wejścia HTTP (idempotency-key na POST).

## Kluczowe pliki

- `framework/<bc>/.../api/{app,router,controller}.py`
- `application/<bc>/.../commands/create_*_command.py`, `command_handlers/create_*_handler.py`
- `domain/<bc>/aggregates/.../aggregate.py`
- `platform/domain/base/aggregate_root.py`
- `platform/application/bus/command_bus.py`
- `platform/infrastructure/persistence/sql_alchemy_uow_base.py`
- `infrastructure/<bc>/.../unit_of_work.py`
- `bootstrap/<bc>/container/*.py`, `bootstrap/<bc>/main.py`
