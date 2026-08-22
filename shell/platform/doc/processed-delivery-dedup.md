# Deduplikacja przez `processed_delivery`

## Cel / Co realizuje

Implementuje jawną deduplikację at-least-once dla handlerów, które nie mogą współdzielić transakcji procesora inbox. Port `DeliveryDedupStore` (w `shell/platform/application/ports/delivery_dedup_store.py`) oraz jego implementacja `ProcessedDeliveryStore` (w `shell/platform/infrastructure/messaging/inbox/processed_delivery_store.py`) wraz z modelem `processed_delivery` (fabryka `build_processed_delivery_model`) umożliwiają: zapis wiersza dedup atomowo z efektem biznesowym oraz sprawdzenie `is_duplicate` przed dispatch, dzięki czemu redelivery nigdy nie wykonuje handlera drugi raz.

## Problem

Processor inbox commituje efekt + outbox + ack w jednej transakcji (session scope — patrz [inbox-processor](inbox-processor.md) i [session-scope](session-scope.md)), więc handlery SQL dzielące sesję procesora nie potrzebują dodatkowego wiersza dedup. Ale są handlery, które **nie mogą** współdzielić transakcji procesora — inna baza danych lub niesdzielony UoW. Dla nich at-least-once oznacza, że awaria między wykonaniem efektu a ackiem spowoduje redelivery; bez dedup handler wykonałby się dwukrotnie. Potrzebny jest trwały znacznik „ten konsument już przetworzył ten delivery", zapisywany atomowo z efektem i konsultowany przed każdym dispatch.

## Realizacja techniczna

### Port — DeliveryDedupStore

`DeliveryDedupStore` to `Protocol` z dwiema metodami:

- `is_duplicate(outbox_id: str) -> bool` — czy ten konsument już przetworzył rekord outbox; sesja rozwiązywana z aktywnego session scope; musi być wołana z transakcji procesora;
- `mark_processed(outbox_id, *, payload=None, processed_at=None) -> None` — rejestruje `outbox_id` jako przetworzony; musi być wywołana atomowo z efektem biznesowym; konflikt klucza unikalnego jest no-op.

### Implementacja — ProcessedDeliveryStore

`ProcessedDeliveryStore(model, consumer_name)` implementuje port. Dwa zestawy metod:

- **Ambient scope** (kontrakt portu): `is_duplicate` / `mark_processed` — sesję pobierają z `get_session_scope()`; brak scope → `RuntimeError` ("ProcessedDeliveryStore requires an active delivery session scope; use is_duplicate_in_session/mark_processed_in_session with an explicit session instead").
- **Z jawną sesją** (procesor, adaptery, testy): `is_duplicate_in_session(session, outbox_id)` i `mark_processed_in_session(session, outbox_id, *, payload, processed_at)`.

`is_duplicate_in_session` wykonuje `select(model.id).where(consumer_name == self._consumer_name, outbox_id == outbox_id)` i zwraca `result.first() is not None`.

`mark_processed_in_session`:

```python
with suppress(IntegrityError):
    await session.execute(
        insert(self._model).values(
            id=_new_id(),
            consumer_name=self._consumer_name,
            outbox_id=outbox_id,
            payload=payload or {},
            processed_at=processed_at or datetime.now(tz=UTC),
        )
    )
```

Konflikt klucza unikalnego na `(consumer_name, outbox_id)` oznacza, że rekord outbox był już przetworzony i jest traktowany jako sukces (no-op) — wiersz dedup **nigdy** nie jest zapisywany w osobnej transakcji przed efektem biznesowym.

### Model `processed_delivery`

`build_processed_delivery_model(base)` tworzy model ORM powiązany z per-BC metadata:

- `__tablename__ = "processed_delivery"`;
- unikalność: `UniqueConstraint("consumer_name", "outbox_id", name="uq_processed_delivery_consumer_outbox")`;
- kolumny: `id` (PK, `str`), `consumer_name` (`str`, nie-null), `outbox_id` (`str`, nie-null), `payload` (`JSONB`, nie-null, default `dict`), `processed_at` (`DateTime(timezone=True)`, nie-null);
- nazwa klasy jest per-registry: `ProcessedDeliveryModel.__name__ = f"{base.__name__}ProcessedDeliveryModel"`.

Unikalność `(consumer_name, outbox_id)` oznacza: ten sam rekord outbox replayowany przez tego samego konsumenta jest zawsze no-op.

### Auto-zapis w tej samej transakcji

`InboxProcessorBase` przyjmuje `processed_delivery_model` + `consumer_name`; gdy oba są ustawione, tworzy `ProcessedDeliveryStore` i w `_process_in_transaction`:

1. **przed dispatch**: `_is_duplicate(session, row.id)` — gdy `True`, rekord jest od razu potwierdzany (`_acknowledge_in_session` + commit, wynik `"processed"`), handler się nie wykonuje;
2. **po skutecznym dispatch** (przed ack): `mark_processed_in_session(session, row.id, payload=...)` — wiersz dedup zapisywany w **tej samej sesji**, co ack i commit, więc jest atomowy z efektem i statusem `PROCESSED`.

Wiersz dedup nie jest tworzony przez procesor dla handlerów dzielących sesję (tam efekt i ack to jeden commit) — jest to jawna ścieżka fallback dla handlerów z osobną bazą / osobnym UoW.

### IntegrityError jako idempotentny no-op

Konflikt `uq_processed_delivery_consumer_delivery` w `mark_processed_in_session` jest łapany przez `suppress(IntegrityError)` — to przypadkek równoległego lub powtórzonego przetworzenia tego samego delivery przez tego samego konsumenta; wynik operacji to sukces, bez propagowania błędu.

## Kluczowe pliki

- `shell/platform/application/ports/delivery_dedup_store.py`
- `shell/platform/infrastructure/messaging/inbox/processed_delivery_store.py`
- `shell/platform/infrastructure/persistence/sql/models/processed_delivery.py`
- `shell/platform/infrastructure/messaging/inbox/inbox_processor_base.py` (współpraca: `_is_duplicate`, `mark_processed_in_session`)

## Powiązane koncepcje

- [inbox-processor](inbox-processor.md)
- [session-scope](session-scope.md)
- [delivery-overview](delivery-overview.md)
- [unit-of-work](unit-of-work.md)
- [retention](retention.md)
- [replay](replay.md)
- [ports-and-adapters](ports-and-adapters.md)
