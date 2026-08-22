---
name: integration-event
description: "Projektowanie IntegrationEvent w SHELL: publiczny kontrakt faktu miedzy bounded contexts, rozdzielenie payloadu biznesowego od metadata envelope, identyfikatory, wersjonowanie i kompatybilnosc. Uzywaj przy dodawaniu lub review eventow integracyjnych, mapperow, outbox/inbox i serializerow."
---

# Integration Event

## Definicja

`IntegrationEvent` jest publiczna reprezentacja faktu domenowego przeznaczona dla innych bounded contexts.

```text
DomainEvent
    fakt wewnatrz BC
        |
        | jawne mapowanie kontraktu
        v
IntegrationEvent
    publiczny fakt dla innych BC
```

IntegrationEvent opisuje publiczny fakt, `Command` wyraza intencje operacji, `Message` przenosi pasywne dane, a koperta transportuje metadane i payload eventu.

Odbiorca reaguje na fakt we wlasnym bounded context i korzysta z publicznego kontraktu IntegrationEvent.

## Zasada zawartosci

IntegrationEvent sklada sie logicznie z dwoch czesci:

1. publicznego faktu, ktory opisuje payload biznesowy;
2. metadata eventu, ktore identyfikuja fakt, jego pochodzenie i schemat.

Transport zapisuje event w kopercie i zachowuje jego semantyke.

## Payload biznesowy

`payload` zawiera wylacznie dane faktu potrzebne konsumentowi:

- identyfikatory i wartosci biznesowe opisujace zaszle zdarzenie;
- snapshot wartosci potrzebnych do reakcji lub projekcji;
- pola opcjonalne zgodne z polityka kompatybilnosci.

Payload opisuje dane faktu. Instrukcje operacji nalezace do Command, konfiguracja transportu, dane ORM, encje agregatu i prywatne Value Objecty pozostaja w odpowiednich kontraktach i warstwach.

Przyklad:

```python
payload = {
    "workflow_id": "workflow-1",
    "status": "COMPLETED",
    "result": "ok",
}
```

Nazwy i typy payloadu sa publicznym kontraktem. Konsument korzysta z jawnego znaczenia pol oraz lokalnego modelu kontraktu.

## Poza payloadem: envelope metadata

Nastepujace pola sa metadata koperty i musza byc przeniesione end-to-end poza `payload`:

| Pole | Znaczenie |
|---|---|
| `event_id` | Tozsamosc logicznego faktu. Mapper zachowuje ID DomainEvent, jesli opisuje ten sam fakt. |
| `event_type` | Stabilna nazwa publicznego kontraktu ustalona przez producenta i konsumentow. |
| `occurred_at` | Czas zajscia faktu, w UTC. |
| `schema_version` | Wersja kontraktu IntegrationEvent, od ktorej zaczyna prace upcaster. |
| `correlation_id` | ID procesu lub lancucha, ktory laczy powiazane komunikaty/fakty. |
| `causation_id` | ID bezposredniego faktu lub bodzca, ktory spowodowal ten event. |
| `aggregate_id` | ID agregatu zrodla, jezeli wymagane do routingu, korelacji lub idempotencji. |
| `aggregate_name` | Stabilna nazwa typu agregatu, jezeli kontrakt jej wymaga. |

Docelowa koperta:

```python
{
    "event_id": "event-1",
    "event_type": "WorkflowCompleted",
    "occurred_at": "2026-08-21T12:00:00+00:00",
    "schema_version": 2,
    "correlation_id": "correlation-1",
    "causation_id": "event-0",
    "aggregate_id": "workflow-1",
    "aggregate_name": "Workflow",
    "payload": {
        "status": "COMPLETED",
        "result": "ok",
    },
}
```

`event_id` identyfikuje fakt, `message_id` identyfikuje Message, a `outbox_id` wskazuje rekord outbox producenta. Rekord inbox ma własne lokalne `id`.

## Lifecycle w SHELL

```text
Aggregate
    -> DomainEvent
    -> UnitOfWork stages only DomainEvent
    -> IntegrationEventMapper
    -> IntegrationEvent contract
    -> IntegrationEventSerializer
    -> outbox envelope
    -> relay
    -> inbox envelope
    -> IntegrationEventDeserializer
    -> consumer handler
```

UoW przechowuje `DomainEvent` w kolekcji staged eventow. Mapowanie do IntegrationEvent odbywa sie na granicy integracji, przy przygotowaniu zapisu do outboxa.

## Odpowiedzialnosci komponentow

- `AggregateRoot`: emituje `DomainEvent` po zmianie stanu.
- `IntegrationEventMapper`: mapuje prywatny DomainEvent na publiczny kontrakt.
- `IntegrationEventSerializer`: serializuje IntegrationEvent do payloadu/koperty zgodnie z kontraktem.
- `Outbox`: zapisuje koperty atomowo z lokalna zmiana domenowa.
- `Relay`: kopiuje koperty z outbox do inbox/brokera i zachowuje payload oraz metadata.
- `IntegrationEventDeserializer`: przyjmuje tylko registry IntegrationEvent, stosuje upcaster i odtwarza kontrakt.
- Konsument: reaguje na fakt we wlasnym BC i zachowuje idempotencje.

## Wersjonowanie

- `schema_version` nalezy do kontraktu IntegrationEvent i opisuje envelope metadata.
- Zmiana znaczenia pola, typu, nazwy lub wymaganej obecnosci wymaga nowej wersji; zmiana znaczenia zwykle wymaga nowej nazwy eventu.
- Dodawaj pola opcjonalne zamiast wymaganych, gdy zachowanie starych konsumentow musi pozostac zgodne.
- Zmiana pola korzysta z polityki deprecacji i potwierdzenia wszystkich konsumentow.
- Upcaster podnosi stary payload do aktualnego modelu przed dispatchingiem.
- Kompletna sciezka `schema_version` w outbox i relay zachowuje informacje o kontrakcie.

## Testy kontraktu

Kazdy publiczny IntegrationEvent powinien miec test w `shell/tests/contracts/`, ktory sprawdza:

- dokladna nazwe `event_type`;
- obecne pola i typy payloadu;
- obecne metadata koperty poza payloadem;
- zachowanie `event_id`, `occurred_at`, `schema_version`, `correlation_id` i `causation_id` przez outbox -> relay -> inbox;
- deserializacje aktualnej wersji;
- upcasting poprzednich wspieranych wersji;
- obsluge wersji znanej i wersji wykraczajacej poza polityke kompatybilnosci;
- idempotentne przetworzenie duplikatu.

## Rozdzielenie kontraktow

Projektuj osobne klasy i registry dla:

```text
IntegrationEvent != DomainMessage != Command
```

Wspolna moze byc niskopoziomowa konwersja wartosci technicznych. Semantyka, registry, schema version, serializer i deserializer musza pozostac rozdzielone wedlug typu kontraktu.

## Stan implementacji SHELL

Aktualny `IntegrationEvent` w platformie zawiera metadata jako pola dataclass, aby mapper i deserializer mogly pracowac typowo. Warstwa envelope przechowuje te pola poza biznesowym `payload`.

Implementacja musi konsekwentnie wydzielac je do envelope. Szczegolnie `schema_version` musi miec kompletna sciezke:

```text
IntegrationEvent.schema_version
    -> outbox
    -> relay
    -> inbox
    -> IntegrationEventDeserializer/upcaster
```

Kod serializujacy metadata do payloadu albo pomijajacy je pomiedzy outbox i inbox wymaga korekty kontraktu.
