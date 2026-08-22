# Outbox transakcyjny

## Cel / Co realizuje

Implementuje wzorzec transactional outbox dla eventów, messages i commands. Stan domeny oraz odpowiedni outbox są zapisywane atomowo przez `SqlAlchemyUnitOfWorkBase.commit()` → `_write_staged_outbox()`, a `OutboxToTransportRelay` publikuje każdy rodzaj przez jeden kontrakt transportowy.

## Problem

Klasyczny dual write — zapis stanu w bazie i wysłanie do brokera w osobnych transakcjach — prowadzi do utraty wiadomości, gdy proces umrze między commitem a publikacją. Outbox przenosi publikację poza transakcję: deliverable jest najpierw trwale zapisane w bazie (atomowo z efektem), a dopiero później przekazywane do transportu przez relay, który po udanym wysłaniu oznacza wiersz jako opublikowany. Dodatkowo każdy wiersz musi nieść kontekst tracingu (`correlation_id`, `causation_id`) oraz wiersz audytowy pozwalający na weryfikację, że nic nie zostało zagubione.

## Realizacja techniczna

### Zapis w jednym UoW

`SqlAlchemyUnitOfWorkBase` (port `UnitOfWork`) gromadzi zdarzenia przez `stage_events()` (a wiadomości przez `stage_messages()`). W `commit()` wywoływany jest `_write_staged_outbox()`, który w tej samej sesji i transakcji:

- mapuje każde zdarzenie przez `ReflectiveIntegrationMapper` do `IntegrationEvent`;
- serializuje IntegrationEvent przez `IntegrationEventSerializer.to_envelope(...)`;
- pobiera `occurred_at` (`event.occurred_at.value`, gdy obiekt ma atrybut `.value`);
- dodaje wiersz outboxa z lokalnym `id` oraz metadanymi envelope;
- dodaje wiersz audytowy: `self._models.audit(id=str(uuid.uuid4()), event_type=event_type, occurred_at=raw_occurred_at, payload=payload)`.

Commit w trybie zwykłym wykonuje `session.commit()`. W trybie deferred (`__aenter__` z aktywnym scope) wykonuje tylko `session.flush()` — fizyczny commit należy do procesora inbox, dzięki czemu efekt + outbox + ack są jednym.

### Zapis message i command poza UoW domenowym

`SqlMessageOutboxPublisher.publish(messages: Sequence[object])` i `SqlCommandOutboxPublisher.publish(...)` zapisują kontrakt do odpowiedniego outboxa, gdy powstaje poza domenowym UoW:

- odczytują kontekst tracingu: `correlation_id = get_correlation_id()`, `causation_id = get_causation_id()`;
- tworzą serializer kontraktu i dla każdego obiektu:
  - `payload = serializer.to_payload(...)`;
  - `session.add(self._outbox_model(id=str(uuid.uuid4()), event_type|message_type=type(obj).__name__, occurred_at=obj.occurred_at.value, payload=payload, correlation_id=correlation_id, causation_id=causation_id, published_at=None))`;
- commit w `async with self._session_factory() as session`.

`SqlCommandOutboxPublisher.publish(command_type, payload, occurred_at)` ma jawniejszy kontrakt — przyjmuje gotowy `command_type` i `payload`, zapisuje wiersz z `correlation_id`/`causation_id` z kontekstu (bez kolumny `published_at` w wywołaniu, bo model komend go nie ma) i commituje.

Publisher message/command pracuje na własnej sesji per wywołanie. Każdy zapisany rekord jest później publikowany wyłącznie przez `OutboxToTransportRelay`. Właścicielem modeli jest per-BC bundle delivery, budowany z platformowych fabryk — patrz [delivery-models](delivery-models.md).

### Nieudana serializacja

W event/message publisherach niepowodzenie `to_payload` jest logowane jako `critical` („Failed to serialize event ... — event LOST") i ponownie podnoszone (`raise`) — wiadomość nigdy nie jest cicho porzucana.

### Rola relaya

Wiersz outboxa zostaje z `published_at=None`; `OutboxToTransportRelay` publikuje go przez broker i dopiero po potwierdzeniu znaczy jako opublikowany. Konsument po drugiej stronie tworzy lokalny rekord inboxa — [inbox-lifecycle](inbox-lifecycle.md).

## Kluczowe pliki

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
