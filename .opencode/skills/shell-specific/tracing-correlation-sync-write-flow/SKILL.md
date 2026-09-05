---
name: tracing-correlation-sync-write-flow
description: Zakres obsługiwany przez ten skill to write path (CQRS write side) — przepływ correlation_id w synchronicznej komendzie: od ustawienia na granicy wejścia (HTTP/CLI) przez CommandBus/handler/agregat, aż do zapisania do eventu (mapper → IntegrationEvent → event_outbox/audit_event). Dostawa cross-BC (relay/broker/inbox/delivery) jest poza tym zakresem. Używaj gdy analizujesz skąd bierze się correlation_id w wierszu event_outbox, debugujesz puste/niepoprawne ID, dodajesz nową komendę synchroniczną albo sprawdzasz czy trace przetrwa od requestu do zapisu eventu.
---

# Observability w kontekście SYNCCHRONICZNEJ komendy — od ustawienia correlation_id do zapisu do eventu

## Cel

Opisuje **jeden konkretny przepływ**: synchroniczna komenda (write side, jeden BC).
Punkt startu: ustawienie `correlation_id` na granicy wejścia.
Punkt końca: zapisanie `correlation_id`/`causation_id` do **eventu** — dokładnie do wiersza `event_outbox` (i `audit_event`), przez mapper `ReflectiveIntegrationMapper`.

> Poza zakresem: dostawa cross-BC (relay/broker/inbox) — zaczyna się dopiero **po** zapisie outboxa.

## Mapa przepływu (sync end-to-end)

```text
1. Wejście: HTTP/CLI
   CorrelationIdMiddleware / install_trace_id_generator
   └─> correlation_id_var (ContextVar)  [USTAWIENIE ID]
2. Controller → CommandBus.dispatch(CreateXCommand)
3. Handler (CreateXHandler) → UnitOfWork
4. Aggregate.create() → append_event(DomainEvent)
5. UoW.save → pull_events() → stage_events()
6. UoW.commit → _write_staged_outbox()
7. ReflectiveIntegrationMapper.map(domain_event)
   └─> correlation_id = get_or_create_correlation_id()   [gdzie ID trafia do eventu]
   └─> causation_id   = get_causation_id()
8. IntegrationEvent(correlation_id, causation_id, ...)
9. event_outbox  (kolumna correlation_id + causation_id)  [KONIEC: zapisane do eventu]
   + audit_event (payload, bez correlation)
```

## Krok 1 — ustawienie correlation_id na granicy wejścia

### Wejście HTTP
`shell/platform/framework/api/middleware/correlation_id.py:26-32`:
- czyta nagłówek `X-Correlation-ID`; jeżeli obecny → używa go;
- jeżeli **brak nagłówka** → `get_or_create_correlation_id()` generuje nowy (UUID) i ustawia;
- `token = set_correlation_id(cid)` (`:32`) — wartość ląduje w ContextVar; reset przy wyjściu (`:44`).

### Wejście CLI / proces spoza HTTP
`shell/platform/bootstrap/tracing.py:install_trace_id_generator()` (wołane w `main.py` każdego BC)
instaluje `CorrelationIdGenerator` do holdera (`application/context/correlation_id.py:39-50`). ID wygeneruje się **leniwie** przy pierwszym zapisie (krok 7) — nigdy nie jest puste.

### Mechanizm ustawiania
`shell/platform/application/context/correlation_id.py`:
- `correlation_id_var: ContextVar[str]` (`:26`);
- `set_correlation_id(value) -> Token` (`:72`), `reset_correlation_id(token)` (`:76`);
- `get_or_create_correlation_id()` (`:57-69`) — zwraca bieżące albo generuje+ustawia; **nigdy `""`**.

## Krok 2 — kontroller i CommandBus

- `Controller.create_x` → `await command_bus.dispatch(CreateXCommand(...))` — np. `framework/<bc>/.../api/controller.py:96-100`.
- `CommandBus.dispatch` → `factory()` → `await handler.handle(command)` — `platform/application/bus/command_bus.py:18-21`.
- ID **nie jest** w payload komendy — siedzi w ambient ContextVar i jest czytane dopiero przy zapisie.

## Krok 3 — handler + UoW

`application/<bc>/.../command_handlers/create_x_handler.py` (np. `create_project_handler.py:33-45`):
- buduje VO, `Aggregate.create(...)`, `async with unit_of_work: await unit_of_work.save(repo, aggregate)`.

## Krok 4 — agregat nagrywa DomainEvent

`domain/<bc>/aggregates/.../aggregate.py` (`Project.create` → `_new`):
- `append_event(DomainEvent)` — `platform/domain/base/aggregate_root.py:27-35` (bufforuje event, nadpisuje `aggregate_id` prawdziwym ID agregatu).

## Krok 5 — pull_events → stage_events

`SqlAlchemyUnitOfWorkBase.save()` — `shell/platform/infrastructure/persistence/sql_alchemy_uow_base.py:111-115`:
- `await repo.save(aggregate)` → `aggregate.pull_events()` (kopiuje bufor) → `stage_events(...)` (do `_staged_events`).

## Krok 6 — commit → _write_staged_outbox

`SqlAlchemyUnitOfWorkBase.commit()` — `sql_alchemy_uow_base.py:142-157`:
- wywołuje `_write_staged_outbox()` (`:159-190`) w **tej samej transakcji** co mutacja;
- dla każdego stage'owanego eventu: `self._mapper.map(domain_event)` (`:164`).

## Krok 7 — mapper: TUTAJ correlation_id trafia do eventu

`shell/platform/infrastructure/mapping/reflective_integration_mapper.py:23-42`:
```
correlation_id = get_or_create_correlation_id()   # :28  — nie-pusto zawsze
causation_id   = get_causation_id()               # :29
event_id       = str(domain_event.event_id.value) # :27
occurred_at    = domain_event.occurred_at.value   # :30
aggregate_id   = str(domain_event.aggregate_id.value)  # :31
schema_version = 1
```
- buduje `IntegrationEvent` (sub)klasę z polami envelope + polami biznesowymi (`:35-40`).
- **To jest jedyny moment w łańcuchu, w którym ID jest zapisywane do obiektu eventu.**

## Krok 8 — serializacja envelopu

`IntegrationEventSerializer.to_envelope(event, source_service=...)` (`infrastructure/serialization/integration_event/integration_event_serializer.py:35-55`) — zwraca dict z `correlation_id`/`causation_id`.

## Krok 9 — KONIEC: zapis do tabeli eventu

`_write_staged_outbox` — `sql_alchemy_uow_base.py:170-190`:
```python
outbox = self._models.events.outbox(
    ...
    correlation_id=envelope["correlation_id"],   # :179
    causation_id=envelope["causation_id"],       # :180
)
self._session.add(outbox)
self._session.add(self._models.audit(...))       # :183-190
```
- **`event_outbox`** — kolumny `correlation_id`, `causation_id` (`NOT NULL`, default `""`) pochodzą z `DeliveryColumnsMixin` w `messaging/delivery/delivery_columns.py:20-21`. **Tu kończy się zapisanie ID do eventu.**
- **`audit_event`** — `models/audit_delivery.py:15-21` — **nie ma kolumny `correlation_id`** (tylko `id`, `integration_event_name`, `occurred_at`, `payload`).

## Osobna ścieżka (komenda cross-BC, producent)

`SqlCommandOutboxWriter.append()` — `messaging/command/sql_command_outbox_writer.py:66-80` zapisuje `command_outbox` z `correlation_id = get_or_create_correlation_id()`, `causation_id = get_causation_id()` (`:77-78`). NIE należy do ścieżki sync lokalnej — tylko gdy handler celowo wysyła intencję do innego BC.

## Skąd dokładnie wartość w wierszu: podsumowanie

| Etap | Plik:linia | Wartość correlation_id |
|---|---|---|
| Ustawienie (HTTP) | `middleware/correlation_id.py:26-32` | nagłówek lub nowy UUID |
| ContextVar | `application/context/correlation_id.py:26` | bieżąca wartość kontekstu |
| Odczyt przy zapisie | `application/context/correlation_id.py:57-69` | bieżąca albo wygenerowana |
| Zapis do eventu | `mapping/reflective_integration_mapper.py:28` | `get_or_create_correlation_id()` |
| Wiersz outboxa | `sql_alchemy_uow_base.py:179` | `envelope["correlation_id"]` |
| Tabela | `messaging/delivery/delivery_columns.py:20-21` | kolumna `correlation_id` (`DeliveryColumnsMixin`) |

## Reguły

1. **ID jest ustawiane raz, na granicy wejścia** (HTTP middleware lub leniwie przy pierwszym zapisie); handler i agregat go nie modyfikują.
2. **Zapis do eventu = mapper** (`get_or_create_correlation_id` w `reflective_integration_mapper.py:28`); surowy `get_correlation_id()` tylko do odczytu.
3. **Never-empty**: jeżeli zapis do outboxa miałby nastąpić bez wcześniejszego ustawienia (np. CLI), `get_or_create` generuje i ustawia — nigdy nie wstawia `""`.
4. **Komenda nie niesie correlation w payload** — ID żyje w ambient ContextVar.
5. **Audit nie ma correlation** — jeśli audyt ma być łączalny z trace, rozszerz model (decyzja, nie domyślność).
6. **Regresja blokowana arch-testem**: `tests/architecture/test_tracing_generator_structure__test_trace_writers_never_produce_empty_correlation_id.py`.

## Kluczowe pliki

- `platform/framework/api/middleware/correlation_id.py`
- `platform/bootstrap/tracing.py` + `platform/application/context/ports/correlation_id_generator.py` + `infrastructure/identity/{uuid,static}_correlation_id_generator.py`
- `platform/application/context/correlation_id.py`
- `platform/application/bus/command_bus.py`
- `platform/infrastructure/mapping/reflective_integration_mapper.py`
- `platform/infrastructure/persistence/sql_alchemy_uow_base.py`
- `platform/infrastructure/serialization/integration_event/integration_event_serializer.py`
- `platform/infrastructure/persistence/sql/models/event_delivery.py`, `audit_delivery.py`
- `platform/infrastructure/messaging/delivery/delivery_columns.py` (`DeliveryColumnsMixin` — kolumny `correlation_id`/`causation_id`)
- `platform/infrastructure/messaging/command/sql_command_outbox_writer.py` (producent cross-BC)