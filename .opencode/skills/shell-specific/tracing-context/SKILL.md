---
name: tracing-context
description: Tracing context (correlation_id / causation_id / event_id / trace_id) w SHELL — ContextVary, propagacja przez outbox/inbox, envelope, logging, gRPC/HTTP. Używaj gdy dodajesz nowy handler produkujący eventy, projektujesz nowy outbox/inbox przepływ, implementujesz integration event listener, albo debugujesz brakującą korelację między eventami.
---

# Tracing Context — correlation_id, causation_id, event_id, trace_id

## Przepływ danych

```
  Request (X-Correlation-ID header)
       │
       ▼
  correlation_id_var.set(...)   ← CorrelationIdMiddleware / gRPC interceptor
       │
       ▼
  Handler tworzy DomainEvent (auto event_id)
       │
     ├─► SqlAlchemyUnitOfWork
       │     └─► outbox_event: [correlation_id, causation_id] ← z ContextVar
       │
       ▼
     OutboxToTransportRelay → broker consumer
       └─► inbox_event: [correlation_id, causation_id] ← kopiowane z outbox
       │
       ▼
  EventInboxProcessor.run_once()
       │
       ├─► correlation_id_var.set(row.correlation_id)
       ├─► causation_id_var.set(domain_event.event_id)   ← causation = ID przetwarzanego eventu
       └─► dispatch do EventBus
             │
             ▼
           Handler może wyprodukować kolejne eventy → cykl
```

## ContextVary

Zdefiniowane w `shell/platform/application/context/`:

| Zmienna | Typ | Default | Znaczenie |
|---------|-----|---------|-----------|
| `correlation_id_var` | `ContextVar[str]` | `""` | Identyfikator całego łańcucha przyczynowego (przychodzi z zewnątrz) |
| `causation_id_var` | `ContextVar[str]` | `""` | ID eventu który spowodował BIEŻĄCE przetwarzanie |

Funkcje dostępu (z tego samego modułu):
- `get_correlation_id()`, `set_correlation_id(val)`, `reset_correlation_id(token)`
- `get_causation_id()`, `set_causation_id(val)`, `reset_causation_id(token)`

## Gdzie ContextVar JEST ustawiane

| Miejsce | Co ustawia | Wartość |
|---------|-----------|---------|
| `CorrelationIdMiddleware` (HTTP) | `correlation_id` | `request.headers["x-correlation-id"]` lub UUID |
| `CorrelationIdAsyncClient` (HTTP out) | `X-Correlation-ID` header | `get_correlation_id()` |
| `EventInboxProcessor.run_once()` | `correlation_id`, `causation_id` | `correlation_id`=z wiersza inbox, `causation_id`=`domain_event.event_id` |
| `CommandInboxProcessor.run_once()` | `correlation_id` | z wiersza inbox; `causation_id` resetowane do `""` |
| `auto_correlation_id` (test fixture) | `correlation_id` | `f"test-{uuid.uuid4()}"` (autouse we wszystkich testach) |

## Gdzie ContextVar JEST odczytywane

| Miejsce | Co czyta | Zapisuje do |
|---------|----------|------------|
| `SqlAlchemyUnitOfWork.commit()` | `correlation_id`, `causation_id` | `outbox_event.correlation_id`, `.causation_id` |
| `SqlCommandOutboxPublisher.publish()` | `correlation_id`, `causation_id` | `outbox_command.correlation_id`, `.causation_id` |
| `SqlAlchemyUnitOfWork.commit()` | `correlation_id`, `causation_id` | `outbox_event` (przez `stage_events`) |
| `SqlAlchemyUnitOfWork.commit()` | `correlation_id` | `Envelope.transport_metadata["correlation_id"]` |
| `graph_execution_entity_to_model()` | `correlation_id` | `graph_execution.correlation_id` |
| `CorrelationIdAsyncClient` | `correlation_id` | HTTP header `X-Correlation-ID` |
| `JsonFormatter.format()` | `correlation_id` | Każda linia loga JSON |

## Modele SQL z kolumnami correlation/causation

| Tabela | Kolumny | Uwagi |
|--------|---------|-------|
| `outbox_event` | `correlation_id`, `causation_id` | Oba `str`, default `""`, non-nullable |
| `inbox_event` | `correlation_id`, `causation_id` | Kopiowane z outbox przez relay |
| `outbox_command` | `correlation_id`, `causation_id` | Analogicznie |
| `inbox_command` | `correlation_id`, `causation_id` | Kopiowane z outbox przez relay |
| `graph_execution` | `correlation_id` | Tylko `correlation_id`, ustawiany przez mapper z ContextVar |
| `workflow` | ~~`correlation_id`~~ | Usunięta w migracji 040 (V2 nie używa) |

## Envelope (Message system — legacy)

> **Uwaga**: `Envelope` w `shell/domain/platform/envelope.py` należy do **starego systemu messaging** (MessageBus). Nowy system eventów (EventBus) nie używa Envelope — tracing context żyje w osobnych kolumnach outbox/inbox.

`Envelope.correlation_id` jest przekazywane przez `transport_metadata["correlation_id"]`
- Ustawiane w `SqlAlchemyUnitOfWork.commit()` przy `Envelope.from_message(correlation_id=get_correlation_id())`

> Kanał Message został usunięty — patrz `docs/messages-removed.md`. Tracing context eventów żyje w osobnych kolumnach `outbox_event`/`inbox_event`.

## Reguły (invariants)

1. **Każde `OutboxEventModel(...)` musi mieć `correlation_id=` i `causation_id=`** — nigdy nie pozwalaj na domyślne `""`
2. **`causation_id` w `EventInboxProcessor` = `event_id` przetwarzanego eventu** — nigdy nie kopiuj starego causation_id
3. **Test `auto_correlation_id` fixture (autouse)** — każdy test ma swój correlation_id

## Testowanie

- `shell/tests/platform/unit/application/test_correlation_id.py` — podstawowy test ContextVar
- `shell/tests/platform/unit/application/test_outbox.py` — `InMemoryOutboxStore` zapisuje correlation/causation
- `shell/tests/platform/architecture/test_tracing_context_structure.py` — AST: pilnuje że `OutboxEventModel` ma correlation_id
