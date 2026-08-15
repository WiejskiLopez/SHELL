# Outbox transakcyjny

## Cel / Co realizuje

Implementuje wzorzec transactional outbox dla trzech typów deliverable: `SqlEventOutboxPublisher` (tabela `outbox_event`), `SqlMessageOutboxPublisher` (tabela `outbox_message`) i `SqlCommandOutboxPublisher` (tabela `outbox_command`). Deliverable są zapisywane w dwóch trybach: (1) atomowo ze stanem domeny w `SqlAlchemyUnitOfWorkBase.commit()` → `_write_staged_outbox()`, który dodatkowo zapisuje wiersz audytowy, oraz (2) przez dedykowane publisherowane sesje z kolumną `published_at=None` pozostawioną do zaznaczenia przez relay.

## Problem

Klasyczny dual write — zapis stanu w bazie i wysłanie do brokera w osobnych transakcjach — prowadzi do utraty wiadomości, gdy proces umrze między commitem a publikacją. Outbox przenosi publikację poza transakcję: deliverable jest najpierw trwale zapisane w bazie (atomowo z efektem), a dopiero później przekazywane do transportu przez relay, który po udanym wysłaniu oznacza wiersz jako opublikowany. Dodatkowo każdy wiersz musi nieść kontekst tracingu (`correlation_id`, `causation_id`) oraz wiersz audytowy pozwalający na weryfikację, że nic nie zostało zagubione.

## Realizacja techniczna

### Zapis w jednym UoW

`SqlAlchemyUnitOfWorkBase` (port `UnitOfWork`) gromadzi zdarzenia przez `stage_events()` (a wiadomości przez `stage_messages()`). W `commit()` wywoływany jest `_write_staged_outbox()`, który w tej samej sesji i transakcji:

- serializuje każde zdarzenie przez `DomainEventSerializer.to_payload(event)`;
- pobiera `occurred_at` (`event.occurred_at.value`, gdy obiekt ma atrybut `.value`);
- dodaje wiersz outboxa:
  - `self._models.events.outbox(id=str(uuid.uuid4()), event_type=type(event).__name__, occurred_at=raw_occurred_at, payload=payload, correlation_id=get_correlation_id(), causation_id=get_causation_id())`;
- dodaje wiersz audytowy: `self._models.audit(id=str(uuid.uuid4()), event_type=event_type, occurred_at=raw_occurred_at, payload=payload)`.

Commit w trybie zwykłym wykonuje `session.commit()`. W trybie deferred (`__aenter__` z aktywnym scope) wykonuje tylko `session.flush()` — fizyczny commit należy do procesora inbox, dzięki czemu efekt + outbox + ack są jednym.

### Publisherowane z dedykowanej sesji

`SqlEventOutboxPublisher.publish(events: Sequence[object])` i `SqlMessageOutboxPublisher.publish(messages: Sequence[object])` działają symetrycznie:

- odczytują kontekst tracingu: `correlation_id = get_correlation_id()`, `causation_id = get_causation_id()`;
- tworzą serializer (`DomainEventSerializer` / `DomainMessageSerializer`) i dla każdego obiektu:
  - `payload = serializer.to_payload(...)`;
  - `session.add(self._outbox_model(id=str(uuid.uuid4()), event_type|message_type=type(obj).__name__, occurred_at=obj.occurred_at.value, payload=payload, correlation_id=correlation_id, causation_id=causation_id, published_at=None))`;
- commit w `async with self._session_factory() as session`.

`SqlCommandOutboxPublisher.publish(command_type, payload, occurred_at)` ma jawniejszy kontrakt — przyjmuje gotowy `command_type` i `payload`, zapisuje wiersz z `correlation_id`/`causation_id` z kontekstu (bez kolumny `published_at` w wywołaniu, bo model komend go nie ma) i commituje.

Wszyscy trzej publisherowie pracują na **własnej sesji per wywołanie** — dzięki temu deliverable przetrwa nawet, gdy transakcja wołającego (handler, komenda) została już zamknięta. Właścicielem modeli jest per-BC bundle delivery (np. `EventDeliveryModels` z `models.outbox`), budowany z platformowych fabryk — patrz [delivery-models](delivery-models.md).

### Nieudana serializacja

W event/message publisherach niepowodzenie `to_payload` jest logowane jako `critical` („Failed to serialize event ... — event LOST") i ponownie podnoszone (`raise`) — wiadomość nigdy nie jest cicho porzucana.

### Rola relaya

Wiersz outboxa zostaje z `published_at=None`; relay (outbox→transport oraz outbox→inbox, w docstringach publisherow `EventOutboxToInboxRelay` / `MessageOutboxToInboxRelay`) czyta taki outbox i po dostarczeniu znaczy wiersz jako opublikowany. Opis w [relay](relay.md). Konsument po drugiej stronie zakłada wiersz inboxa — [inbox-lifecycle](inbox-lifecycle.md).

## Kluczowe pliki

- `shell/platform/infrastructure/messaging/event/sql_event_outbox_publisher.py`
- `shell/platform/infrastructure/messaging/message/sql_message_outbox_publisher.py`
- `shell/platform/infrastructure/messaging/command/sql_command_outbox_publisher.py`
- `shell/platform/infrastructure/persistence/sql_alchemy_uow_base.py` (`_write_staged_outbox`)
- `shell/platform/application/ports/unit_of_work.py` (`UnitOfWork`)

## Powiązane koncepcje

- [delivery-overview](delivery-overview.md)
- [relay](relay.md)
- [unit-of-work](unit-of-work.md)
- [tracing-context](tracing-context.md)
- [delivery-models](delivery-models.md)
- [inbox-lifecycle](inbox-lifecycle.md)
- [session-scope](session-scope.md)
