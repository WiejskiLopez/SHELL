# Outbox transakcyjny

## Cel / Co realizuje

Implementuje wzorzec transactional outbox dla eventów (atomowo ze stanem domeny) i komend (niezależny zapis poza UoW). Stan domeny oraz odpowiedni outbox są zapisywane atomowo przez `SqlAlchemyUnitOfWorkBase.commit()` → `_write_staged_outbox()`, a `OutboxToTransportRelay` publikuje każdy rodzaj przez jeden kontrakt transportowy.

## Problem

Klasyczny dual write — zapis stanu w bazie i wysłanie do brokera w osobnych transakcjach — prowadzi do utraty wiadomości, gdy proces umrze między commitem a publikacją. Outbox przenosi publikację poza transakcję: deliverable jest najpierw trwale zapisane w bazie (atomowo z efektem), a dopiero później przekazywane do transportu przez relay, który po udanym wysłaniu oznacza wiersz jako opublikowany. Dodatkowo każdy wiersz musi nieść kontekst tracingu (`correlation_id`, `causation_id`) oraz wiersz audytowy pozwalający na weryfikację, że nic nie zostało zagubione.

## Realizacja techniczna

### Zapis w jednym UoW

`SqlAlchemyUnitOfWorkBase` (port `UnitOfWork`) gromadzi zdarzenia przez `stage_events()`. W `commit()` wywoływany jest `_write_staged_outbox()`, który w tej samej sesji i transakcji:

- mapuje każde zdarzenie przez `ReflectiveIntegrationMapper` do `IntegrationEvent`;
- serializuje IntegrationEvent przez `IntegrationEventSerializer.to_envelope(...)`;
- pobiera `occurred_at` (`event.occurred_at.value`, gdy obiekt ma atrybut `.value`);
- dodaje wiersz outboxa z lokalnym `id` oraz metadanymi envelope;
- dodaje wiersz audytowy: `self._models.audit(id=str(uuid.uuid4()), event_type=event_type, occurred_at=raw_occurred_at, payload=payload)`.

Commit w trybie zwykłym wykonuje `session.commit()`. W trybie deferred (`__aenter__` z aktywnym scope) wykonuje tylko `session.flush()` — fizyczny commit należy do procesora inbox, dzięki czemu efekt + outbox + ack są jednym.

### Zapis command poza UoW domenowym

`SqlCommandOutboxPublisher.publish(...)` zapisuje komendę do outboxa, gdy powstaje poza domenowym UoW:

- odczytuje kontekst tracingu: `correlation_id = get_correlation_id()`, `causation_id = get_causation_id()`;
- zapisuje wiersz z `command_type`, `payload`, `correlation_id`/`causation_id` z kontekstu i commituje we własnej sesji per wywołanie.
- Każdy zapisany rekord jest później publikowany wyłącznie przez `OutboxToTransportRelay`. Właścicielem modeli jest per-BC bundle delivery, budowany z platformowych fabryk — patrz [delivery-models](delivery-models.md).

### Nieudana serializacja

W publisherach niepowodzenie serializacji jest logowane jako `critical` i ponownie podnoszone (`raise`) — wiadomość nigdy nie jest cicho porzucana.

### Rola relaya

Wiersz outboxa zostaje z `published_at=None`; `OutboxToTransportRelay` publikuje go przez broker i dopiero po potwierdzeniu znaczy jako opublikowany. Konsument po drugiej stronie tworzy lokalny rekord inboxa — [inbox-lifecycle](inbox-lifecycle.md).

## Kluczowe pliki

- `shell/platform/infrastructure/messaging/command/sql_command_outbox_publisher.py`
- `shell/platform/infrastructure/persistence/sql_alchemy_uow_base.py` (`_write_staged_outbox`)
- `shell/platform/application/ports/persistence/unit_of_work.py` (`UnitOfWork`)

## Powiązane koncepcje

- [delivery-overview](delivery-overview.md)
- [relay](relay.md)
- [unit-of-work](unit-of-work.md)
- [tracing-context](tracing-context.md)
- [delivery-models](delivery-models.md)
- [inbox-lifecycle](inbox-lifecycle.md)
- [session-scope](session-scope.md)
