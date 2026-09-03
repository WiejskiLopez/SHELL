# Tracing Context

## Cel / Co realizuje

Przenosi identyfikatory korelacji przez cały przepływ delivery:
`correlation_id` (identyfikuje cały łańcuch zdarzeń/wiadomości) oraz
`causation_id` (identyfikuje zdarzenie bezpośrednio je wywołujące). Oba są
przechowywane w `ContextVar` i przepisywane z aktywnego kontekstu do wierszy
outboxu podczas zapisu transakcji — dzięki temu każde zdarzenie wychodzące zna
swojego rodzica.

## Problem

W rozproszonym systemie event-driven pojedynczy zapis biznesowy może wygenerować
łańcuch zdarzeń przechodzący przez outbox, relay, transport i inbox wielu BC.
Bez wspólnego identyfikatora nie da się połączyć zdarzeń w jeden przepływ,
debugować przyczyny ani prześledzić zależności przyczynowo-skutkowych.
Przekazywanie ID jako jawnych parametrów każdego wywołania zanieczyściłoby
sygnatury metod domenowych i aplikacyjnych.

## Realizacja techniczna

### Definicja — `shell/platform/application/context/`

- `correlation_id.py`:
  - `correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")`;
  - `get_correlation_id() -> str`, `set_correlation_id(value) -> Token[str]`,
    `reset_correlation_id(token)` (wzorzec set/reset z `Token`);
  - `get_or_create_correlation_id() -> str` — zwraca bieżący `correlation_id`,
    a gdy jest pusty generuje nowy przez skonfigurowany
    `CorrelationIdGenerator` i ustawia go w kontekście. Używany przez
    wszystkie miejsca **zapisujące** trace (mapper, command outbox writer,
    publisher) — dzięki temu outbox nigdy nie otrzymuje pustego
    identyfikatora przy wejściu spoza HTTP (CLI, worker, test).
  - `set_correlation_id_generator(generator)` — wymienny backend generowania
    (adapter `CorrelationIdGenerator`); ustawiany w Composition Root przez
    `shell/platform/bootstrap/tracing.py:install_trace_id_generator()`.
- `causation_id.py`:
  - `causation_id_var: ContextVar[str] = ContextVar("causation_id", default="")`;
  - `get_causation_id()`, `set_causation_id(value) -> Token[str]`,
    `reset_causation_id(token)` — identyczny kształt API.
- `session_scope.py` — osobny `ContextVar` dla scope'a transakcji delivery,
  patrz [session-scope](session-scope.md).

### Port i adaptery — wymienność backendu

- **Port**: `shell/platform/application/context/ports/correlation_id_generator.py`
  (`CorrelationIdGenerator.generate() -> str`).
- **Adaptery**: `shell/platform/infrastructure/identity/uuid_correlation_id_generator.py`
  (`UuidCorrelationIdGenerator` — domyślny, UUID4) oraz
  `shell/platform/infrastructure/identity/static_correlation_id_generator.py`
  (`StaticCorrelationIdGenerator` — deterministyczny, do testów).
- **Instalacja**: `shell/platform/bootstrap/tracing.py:install_trace_id_generator()`
  wołany na starcie każdego BC (HTTP i worker).

### Re-export — `shell/platform/infrastructure/context/__init__.py`

Moduł infrastruktury re-exportuje całe API z `application.context`:
`DeliverySessionScope`, `correlation_id_var`, `causation_id_var`,
`get_correlation_id`, `get_causation_id`, `get_session_scope`,
`reset_correlation_id`, `reset_causation_id`, `reset_session_scope`,
`session_scope_var`, `set_correlation_id`, `set_causation_id`,
`set_session_scope` (`__all__`). Infrastruktura (np. UoW, outbox) importuje
identyfikatory z `shell.platform.infrastructure.context`.

### Zapis do outboxu — `SqlAlchemyUnitOfWorkBase._write_staged_outbox()`

Podczas commita każde stage'owane zdarzenie jest zapisywane z aktualnymi
wartościami kontekstu:

```
outbox = self._models.events.outbox(
    id=str(uuid.uuid4()),
    event_type=event_type,
    occurred_at=raw_occurred_at,
    payload=payload,
    correlation_id=get_correlation_id(),
    causation_id=get_causation_id(),
)
```

Kolumny `correlation_id` i `causation_id` (tabela `outbox_event` — model w
`event_delivery.py`) mają domyślne `""`. Ta sama para ID trafia do modelu
inboxu (`inbox_event`) przy odbiorze delivery, dzięki czemu ID przeskakuje
przez granicę BC w `DeliveryEnvelope` (`delivery_transport.py` zawiera pola
`correlation_id` i `causation_id`).

Semantyka: `correlation_id` jest stabilny dla całego łańcucha (wspólny dla
zdarzenia źródłowego i wszystkich pochodnych), a `causation_id` wskazuje
konkretne zdarzenie, którego obsługa wyprodukowała dany zapis.

## Kluczowe pliki

- `shell/platform/application/context/correlation_id.py`
- `shell/platform/application/context/causation_id.py`
- `shell/platform/application/context/session_scope.py`
- `shell/platform/infrastructure/context/__init__.py`
- `shell/platform/infrastructure/persistence/sql_alchemy_uow_base.py`
- `shell/platform/infrastructure/persistence/sql/models/event_delivery.py`
- `shell/platform/application/ports/delivery_transport.py`

## Powiązane koncepcje

- [session-scope](session-scope.md)
- [transactional-outbox](transactional-outbox.md)
- [inbox-lifecycle](inbox-lifecycle.md)
- [delivery-models](delivery-models.md)
- [logging](logging.md)
- [unit-of-work](unit-of-work.md)
