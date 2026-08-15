# Unit of Work

## Cel / Co realizuje

Definiuje kontrakt transakcyjnej jednostki pracy (port `UnitOfWork`) oraz
wspólną implementację bazową `SqlAlchemyUnitOfWorkBase`, z której dziedziczą
UoW poszczególnych bounded contextów. UoW zarządza sesją SQLAlchemy, kolekcją
zdarzeń/message stage'owanych do outboxu, zapisem agregatów oraz zamykaniem
transakcji (commit/rollback), a w trybie deferred — odłożeniem commita do
transakcji należącej do delivery processora (sesja z
[DeliverySessionScope](session-scope.md)).

## Problem

Bez UoW każdy handler komendy musiałby sam zarządzać sesją, transakcją,
zapisem zdarzeń domenowych i gwarancją atomowości. Dodatkowo integracja
oparta na transactional outbox wymaga, aby **zmiana biznesowa + wiersz outboxu
+ potwierdzenie inbox** (ack) zostały zapisane w **jednej** transakcji —
najprościej przez współdzielenie sesji między handlerem a delivery processorem.

## Realizacja techniczna

### Port — `shell/platform/application/ports/unit_of_work.py`

`UnitOfWork(Protocol)` deklaruje:

- `repository(repo_type) -> Any` — dostęp do repozytorium po typie portu;
- `stage_events(events: Sequence[object])` i `stage_messages(messages: list[object])`
  — buforowanie zdarzeń/message do zapisu w outboxie;
- `async save(repo_type, aggregate)` — zapis agregatu;
- `events -> Sequence[object]` — odczyt stage'owanych zdarzeń;
- `async commit()`, `async rollback()`;
- `async __aenter__ / __aexit__` — protokół async context managera (konwencja
  `async with unit_of_work:`).

### Implementacja bazowa — `shell/platform/infrastructure/persistence/sql_alchemy_uow_base.py`

`SqlAlchemyUnitOfWorkBase(UnitOfWork)`:

- konstruktor przyjmuje `session_factory: async_sessionmaker[AsyncSession]`,
  `models: PersistenceDeliveryModels | None` (wymagane — `ValueError`, gdy
  `None`) i opcjonalny `mapper`;
- stan: `_staged_events`, `_staged_messages`, `_committed`,
  `_deferred_commit`, `_session`.

Kluczowe metody:

- `_build_repo_map()` — jedyna metoda, którą **podklasa MUSI nadpisać**;
  zwraca `dict[DomainRepo, SqlRepo]` (domyślnie `{}`).
- `repository(repo_type)` — buduje mapę przez `_build_repo_map()`, tworzy
  adapter `sql_type(self._active_session)`; nieznany typ kończy się
  `ValueError("Unknown repository type for this BC: ...")`.
- `save(repo_type, aggregate)` — zapisuje agregat przez repozytorium, potem
  `aggregate.pull_events()` (bufory zdarzeń z `AggregateRoot`); gdy podano
  `mapper`, mapuje każde zdarzenie `self._mapper.map(e)` i stage'uje wynik,
  w przeciwnym razie stage'uje surowe zdarzenia.
- `__aenter__` — pobiera `get_session_scope()`:
  - gdy scope aktywny → `self._session = scope.session`, `_deferred_commit = True`
    (delivery processor jest właścicielem transakcji);
  - w przeciwnym razie → `self._session = self._factory()`, `await __aenter__`,
    `_deferred_commit = False`.
- `__aexit__(*args)` — gdy brak wyjątku i nie było commita → `await self.commit()`;
  gdy `not _deferred_commit` → zamyka sesję przez `await self._session.__aexit__(*args)`.
- `commit()` — najpierw `await self._write_staged_outbox()`, potem:
  - deferred: `await self._session.flush()` (materializacja zmian w wspólnej
    transakcji — realny commit należy do processora);
  - nie-deferred: `await self._session.commit()`;
  następnie czyści bufor zdarzeń/message i ustawia `_committed = True`.
  Wyjątek `StaleDataError` (konflikt wersji optimistic locking) → `rollback()`
  sesji i podniesienie `ConcurrentModificationError("Aggregate", str(exc))`
  z `shell/platform/domain/exceptions/concurrent_modification_error.py`.
- `rollback()` — `await self._session.rollback()`, czyści bufory, a przy
  `_deferred_commit` ustawia `scope.rolled_back = True` — sygnał dla processora,
  by przerwać transakcję i zaplanować retry zamiast ack.
- `_write_staged_outbox()` — dla każdego stage'owanego zdarzenia buduje payload
  przez `DomainEventSerializer().to_payload(event)` (pomija pola `occurred_at`
  i `schema_version`), pobiera `event_type = type(event).__name__`, `occurred_at`
  (`.value` gdy wartość ma atrybut `.value`, np. `CreatedAt`) i zapisuje:
  - wiersz outboxu `self._models.events.outbox(id=str(uuid.uuid4()), event_type=...,
    occurred_at=..., payload=..., correlation_id=get_correlation_id(),
    causation_id=get_causation_id())` — tabela `outbox_event` (`event_delivery.py`);
  - wiersz audytu `self._models.audit(id=str(uuid.uuid4()), event_type=...,
    occurred_at=..., payload=...)`.
  Uwaga: bazowa klasa serializuje wyłącznie `_staged_events`; `stage_messages`
  jest częścią protokołu (bufor `_staged_messages`) dla podklas obsługujących
  osobne outboxy message/command.

Modele persistence: `PersistenceDeliveryModels` (NamedTuple z
`events/messages/commands/audit/processed_delivery/worker_heartbeat`) buduje
`build_persistence_delivery_models(base)` z
`shell/platform/infrastructure/persistence/sql/models/persistence_delivery.py`.

## Kluczowe pliki

- `shell/platform/application/ports/unit_of_work.py`
- `shell/platform/infrastructure/persistence/sql_alchemy_uow_base.py`
- `shell/platform/infrastructure/persistence/sql/models/persistence_delivery.py`
- `shell/platform/infrastructure/persistence/sql/models/event_delivery.py`
- `shell/platform/infrastructure/serialization/event_serializer.py`
- `shell/platform/domain/exceptions/concurrent_modification_error.py`
- `shell/platform/domain/base/aggregate_root.py`

## Powiązane koncepcje

- [session-scope](session-scope.md)
- [transactional-outbox](transactional-outbox.md)
- [inbox-processor](inbox-processor.md)
- [tracing-context](tracing-context.md)
- [aggregate-root](aggregate-root.md)
- [domain-event](domain-event.md)
- [sqlalchemy-persistence](sqlalchemy-persistence.md)
