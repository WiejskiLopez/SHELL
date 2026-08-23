---
name: event-semantics
description: "Semantyka Event w architekturze SHELL: niemutowalny fakt, ktory zaszedl. Uzywaj przy projektowaniu DomainEvent, IntegrationEvent, mapperow, outbox/inbox i handlerow eventow."
---

# Event Semantics

## Definicja

`Event` opisuje fakt, ktory juz zaszedl. Payload eventu zawiera dane faktu.

Fakt to doslowna, prawdziwa tresc tego skilla: `Event -> fakt: "stalo sie"`. Semantyka Command i Message zyje w osobnych skillach (`command-semantics`, `message-semantics`).

## Dwa poziomy eventu

```text
DomainEvent
    fakt wewnatrz jednego bounded contextu

IntegrationEvent
    publiczna reprezentacja tego samego faktu dla innych bounded contexts
```

Oba poziomy maja semantyke faktu.

## Przeplyw

```text
Aggregate
    -> DomainEvent
    -> UnitOfWork stages DomainEvent
    -> IntegrationEventMapper
    -> IntegrationEvent
    -> EventSerializer
    -> outbox/inbox/event transport
```

UoW przechowuje `DomainEvent`. Mapowanie odbywa sie na granicy integracji, przy przygotowaniu zapisu do outboxa. Kolekcja staged eventow ma typ `DomainEvent`.

## Tozsamosc

- `event_id` identyfikuje fakt biznesowy.
- Jesli IntegrationEvent jest reprezentacja tego samego faktu, zachowuje ten sam `event_id`.
- Event posiada tozsamosc faktu, a koperta posiada tozsamosc dostarczenia (patrz `integration-patterns/event-driven-integration`).

## Metadata i payload

- `occurred_at` opisuje czas zajscia faktu.
- `schema_version` opisuje schemat eventu.
- Obie wartosci sa metadata event envelope i musza byc przeniesione end-to-end poza payloadem biznesowym.
- Payload zawiera dane faktu.

## Niezmiennosc i emisja

- Event jest niemutowalny.
- Aggregate Root emituje event po zmianie stanu.
- Event przejscia stanu emituje sie bezwarunkowo, jesli przejscie faktycznie nastapilo.
- Handler eventu reaguje na fakt i zachowuje znaczenie odebranego eventu.

## Izolacja kontraktow

- `DomainEvent` ma osobny model i lifecycle od `IntegrationEvent`.
- Registry, serializer i deserializer eventow obsluguja kontrakty DomainEvent oraz IntegrationEvent.
- `IntegrationEvent` nalezy do publicznego kontraktu BC; jego schema version i kompatybilnosc sa testowane w `shell/tests/contracts/`.
- Kazdy publiczny IntegrationEvent ma jawne mapowanie z DomainEvent. Event internal-only ma jawnie oznaczony lokalny lifecycle.
