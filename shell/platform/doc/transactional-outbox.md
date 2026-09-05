# Outbox transakcyjny

## Cel / Co realizuje

Implementuje wzorzec transactional outbox dla eventów (atomowo ze stanem domeny) i komend delivery (dopisywanych do wspólnej transakcji UoW handlera przez `SqlCommandDeliveryDispatcher`/`SqlCommandOutboxWriter`). Stan domeny oraz odpowiedni outbox są zapisywane atomowo przez `SqlAlchemyUnitOfWorkBase.commit()` → `_write_staged_outbox()`, a `EventOutboxRelay`/`CommandOutboxRelay` publikują każdy rodzaj przez właściwy transport.

## Problem

Klasyczny dual write — zapis stanu w bazie i wysłanie do brokera w osobnych transakcjach — prowadzi do utraty wiadomości, gdy proces umrze między commitem a publikacją. Outbox przenosi publikację poza transakcję: deliverable jest najpierw trwale zapisane w bazie (atomowo z efektem), a dopiero później przekazywane do transportu przez relay, który po udanym wysłaniu oznacza wiersz jako opublikowany. Dodatkowo każdy wiersz musi nieść kontekst tracingu (`correlation_id`, `causation_id`) oraz wiersz audytowy pozwalający na weryfikację, że nic nie zostało zagubione.

## Realizacja techniczna

### Zapis w jednym UoW (eventy)

`SqlAlchemyUnitOfWorkBase` (port `UnitOfWork`) gromadzi zdarzenia przez `stage_events()`. W `commit()` wywoływany jest `_write_staged_outbox()`, który w tej samej sesji i transakcji:

- mapuje każde zdarzenie przez `ReflectiveIntegrationMapper` do `IntegrationEvent`;
- serializuje IntegrationEvent przez `IntegrationEventSerializer.to_envelope(...)` (z `source_service`);
- buduje wiersz outboxa z lokalnym `id` (`_id_generator.new_id()`) oraz wartościami z envelope (`event_id`, `source_service`, `integration_event_name`, `occurred_at`, `aggregate_id`, `schema_version`, `payload`, `correlation_id`, `causation_id`);
- dodaje wiersz audytowy: `self._models.audit(id=..., integration_event_name=..., occurred_at=..., payload=...)`.

Commit w trybie zwykłym wykonuje `session.commit()`. W trybie deferred (`__aenter__` z aktywnym scope) wykonuje tylko `session.flush()` — fizyczny commit należy do procesora inbox, dzięki czemu efekt + outbox + ack są jednym.

### Zapis command delivery (atomy z UoW handlera)

Komendy delivery produkuje wyłącznie warstwa `process` (saga) przez port `CommandDeliveryDispatcher`:

- `SqlCommandDeliveryDispatcher.dispatch(command, *, target_service)` rozwiązuje `CommandContract` po `type(command)`, waliduje `target_service`, serializuje payload z pól dataclass i woła `SqlCommandOutboxWriter.append(scope.session, ...)`;
- `SqlCommandOutboxWriter.append` zapisuje wiersz `command_outbox` (`command_id`, `command_name`, `source_service`, `target_service`, `schema_version`, `issued_at`, `payload`, `correlation_id = get_or_create_correlation_id()`, `causation_id = get_causation_id()`) **bez commita** — dopisanie jest atomowe z transakcją UoW handlera (wymaga aktywnego `DeliverySessionScope`).
- Każdy zapisany rekord jest później publikowany wyłącznie przez właściwy relay (`EventOutboxRelay`/`CommandOutboxRelay`). Właścicielem modeli jest per-BC bundle delivery, budowany z platformowych fabryk — patrz [delivery-models](delivery-models.md).

### Nieudana serializacja

Niepowodzenie serializacji/publikacji jest logowane jako `critical` i ponownie podnoszone (`raise`) — wiadomość nigdy nie jest cicho porzucana.

### Rola relaya

Wiersz outboxa zostaje z `published_at=None`; `EventOutboxRelay`/`CommandOutboxRelay` publikuje go przez broker i dopiero po potwierdzeniu znaczy jako opublikowany. Konsument po drugiej stronie tworzy lokalny rekord inboxa — [inbox-lifecycle](inbox-lifecycle.md).

## Kluczowe pliki

- `shell/platform/infrastructure/messaging/command/sql_command_outbox_writer.py` (`SqlCommandOutboxWriter`, `SqlCommandDeliveryDispatcher`)
- `shell/platform/infrastructure/persistence/sql_alchemy_uow_base.py` (`_write_staged_outbox`)
- `shell/platform/application/ports/persistence/unit_of_work.py` (`UnitOfWork`)
- `shell/platform/infrastructure/serialization/integration_event/integration_event_serializer.py`

## Powiązane koncepcje

- [delivery-overview](delivery-overview.md)
- [relay](relay.md)
- [unit-of-work](unit-of-work.md)
- [tracing-context](tracing-context.md)
- [delivery-models](delivery-models.md)
- [inbox-lifecycle](inbox-lifecycle.md)
- [session-scope](session-scope.md)