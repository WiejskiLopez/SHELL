---
name: message-semantics
description: "Semantyka Message w architekturze SHELL: pasywny obiekt danych przenoszacy wartosci. Uzywaj przy projektowaniu, review lub serializacji DomainMessage i IntegrationMessage."
---

# Message Semantics

## Definicja

`Message` jest pasywnym obiektem danych. Przenosi wartosci potrzebne odbiorcy i zachowuje semantyke danych.

Message przenosi dane potrzebne odbiorcy i zachowuje pasywna semantyke danych.

## Rozdzielenie od Command i Event

```text
Command -> "wykonaj te operacje"
Event   -> "ten fakt juz zaszedl"
Message -> "oto dane"
```

`Message`, `Command` i `Event` maja osobne semantyki, kontrakty i kanaly.

## Wlasnosc i kanaly

- `DomainMessage` i `IntegrationMessage` maja osobne kontrakty od `DomainEvent` i `IntegrationEvent`.
- Message ma osobny registry, serializer, deserializer, bus, outbox i inbox.
- `message_id` identyfikuje dane Message, a `event_id` identyfikuje fakt Event.
- Referencja do `event_id` w kontrakcie Message opisuje powiazanie danych z faktem.
- `schema_version` Message dotyczy schematu danych Message i jest niezalezny od wersji schematu eventu.

## Pola czasu

Pole czasu w Message opisuje techniczny czas utworzenia, wyslania lub odebrania danych. Pole `occurred_at` opisuje czas zajscia faktu Event. Nowe kontrakty stosuja nazwe zgodna z semantyka, np. `created_at`, `sent_at` lub `received_at`.

## Implementacja

- Message przenosi dane pomiedzy komponentami.
- Handler Message zapisuje dane albo przekazuje je dalej.
- Decyzja biznesowa nalezy do agregatu, Command Handlera albo osobnego komponentu domenowego.
- `MessageSerializer` i `MessageDeserializer` maja osobny kontrakt od serializerow i deserializerow eventow.
- Wspolna konwersja wartosci technicznych zachowuje osobne kontrakty semantyczne.

## Istniejacy kod

`DomainMessage` i `IntegrationMessage` sa kontraktami danych platformy. Ich techniczne pola definiuja osobny lifecycle, registry, serializer i deserializer. Zmiana semantyki korzysta z osobnego kontraktu i testu.
