# Wersjonowanie schematu dostaw (EnvelopeValidator, PayloadUpcaster, deserializery)

## Cel / Co realizuje

Mechanizm wersjonowania i walidacji schematu payloadu dostaw. `EnvelopeValidator` (`shell/platform/infrastructure/messaging/inbox/envelope_validator.py`) klasyfikuje problemy kontraktowe koperty (nieznana wersja schematu, brak wymaganych ID, za duży payload) do jawnych kodów błędów zanim rekord trafi do deserializacji. `PayloadUpcaster` (`shell/platform/infrastructure/serialization/upcaster.py`) migruje payload z wersji N do N+1 łańcuchem transformacji, dzięki czemu deserializery zawsze budują aktualny kształt obiektu. `EventDeserializer`, `MessageDeserializer` i `CommandDeserializer` odtwarzają obiekty domenowe z payloadu przy współpracy registry typów.

## Problem

Integracje ewoluują: schemat payloadu danego typu dostawy zmienia się w czasie. Konsument musi odczytywać wiadomości w wielu wersjach (aktualna i poprzednia przez upcaster), ale nie może cicho odrzucać ani crashować na nieznanych wersjach. Błędy kontraktowe (nieznana wersja, za duży payload, brakujący `outbox_id`) nie mogą być maskowane jako generyczne błędy handlera — processor musi je klasyfikować do polityki retry/DLQ. Równolegle deserializacja musi być deterministyczna: typ kontraktu → klasa (registry), payload → argumenty konstruktora z poprawną konwersją typów.

## Realizacja techniczna

### Kody błędów i polityka

Stałe kodów w `envelope_validator.py`: `DESERIALIZATION_ERROR`, `UNSUPPORTED_SCHEMA_VERSION`, `INVALID_ENVELOPE`, `PAYLOAD_TOO_LARGE`, `MISSING_OUTBOX_ID`, `MISSING_CORRELATION_ID`, `MISSING_CAUSATION_ID`.

`EnvelopeValidationPolicy` (frozen dataclass z `slots=True`):

- `supported_schema_versions: Mapping[str, frozenset[int]]` — dozwolone wersje per nazwa typu dostawy (konsument obsługuje aktualną i poprzednią przez upcaster);
- `default_supported_versions: frozenset[int] = frozenset({1})` — dla typów nie wymienionych w mapie;
- `max_payload_bytes: int = 1_000_000`;
- `require_outbox_id: bool = True`, `require_correlation_id: bool = False`, `require_causation_id: bool = False`.

`EnvelopeValidator.validate(*, outbox_id, contract_type, schema_version, payload, correlation_id, causation_id) -> str | None` — w kolejności: brak `outbox_id` → `MISSING_OUTBOX_ID` (gdy wymagany), brak correlation/causation → odpowiednie `MISSING_*`, `schema_version not in supported` → `UNSUPPORTED_SCHEMA_VERSION`, a rozmiar payloadu mierzony przez `_measure_payload` ponad `max_payload_bytes` → `PAYLOAD_TOO_LARGE`. Nieprawidłowa koperta nigdy nie rzuca — zwraca strukturę błędu, którą processor mapuje na retry/DLQ.

`envelope_policy_from_catalog(catalog: ContractCatalog, *, default_supported_versions=None) -> EnvelopeValidationPolicy` — buduje politykę z katalogu kontraktów BC: `supported_schema_versions` każdego wpisu staje się per-typowej allowlistą (`entry.type_name: entry.supported_schema_versions`), co czyni katalog jedynym źródłem prawdy o akceptowanych wersjach.

`_measure_payload(payload) -> int` — szacuje rozmiar bajtowy rekurencyjnie po wartościach (str kodowane UTF-8, prymitywy przez repr, zagnieżdżone dict/list).

### PayloadUpcaster

`shell/platform/infrastructure/serialization/upcaster.py`:

- `PayloadTransform = Callable[[dict[str, object]], dict[str, object]]`;
- registry `_transforms: Mapping[str, Mapping[int, PayloadTransform]]` — mapa `type -> {source_version: transform}`;
- `upcast(type_name, schema_version, payload) -> tuple[dict, int]` — iteruje `while version in versions: payload = versions[version](payload); version += 1`, zwraca payload i wersję końcową; konsument wspiera wersję aktualną i poprzednią — zbyt nowe wersje odrzuca wcześniej `EnvelopeValidator` (`UNSUPPORTED_SCHEMA_VERSION`);
- `has_upcaster(type_name) -> bool`.

### Serializery i deserializery

`DomainEventSerializer` (`serialization/event_serializer.py`): `to_payload(event)` (pomija `occurred_at`, `schema_version`), `to_outbox_payload(event)` (dokument `{id, event_type, occurred_at, payload}`), `from_payload(event_cls, occurred_at, payload, schema_version=1)` — buduje obiekt z `SchemaVersion(schema_version)` i konwersją typów (`CreatedAt`, datetime, list/dict, zagnieżdżone dataclass) przez `_serialize_value`/`_deserialize_value`.

`DomainMessageSerializer` (`serialization/message_serializer.py`): analogiczny, dodatkowo obsługuje `OccurredAt` i używa `get_type_hints(cls)` do rozstrzygania typów pól (`_resolve_hints`).

Deserializery:

- `EventDeserializer` (`serialization/event_deserializer.py`): `deserialize(event_type, occurred_at, payload, schema_version=1)` — szuka klasy w `_registry`, nieznany typ → log `Unknown event type` i `None`; przy `upcaster` wykonuje upcast, potem `self._serializer.from_payload(...)`; błędy `KeyError/ValueError/TypeError` → log `Failed to deserialize event` i `None`.
- `MessageDeserializer` (`serialization/message_deserializer.py`): ten sam przepływ z `DomainMessageSerializer`.
- `CommandDeserializer` (`messaging/serialization/command_deserializer.py`): `deserialize(command_type, payload, schema_version=1)` — `cls = registry.get(command_type)`, brak klasy → `None`; przy upcasterze najpierw upcast, potem `cls(**payload)` (komenda budowana bezpośrednio z payloadu).

### Registry

- `build_type_registry(types) -> dict[str, type]` w `serialization/type_registry.py` — rejestr kluczowany nazwą klasy: `{item.__name__: item for item in types}`;
- `build_event_registry(event_types)` w `serialization/event_registry.py` — otoczka `build_type_registry`; `discover_event_types(package_name, base_type)` — odkrywa klasy w `integration_events/*.py` poniżej pakietu aplikacji BC (importlib + rglob), pomijając `__init__.py` i klasy spoza modułu;
- `build_message_registry(message_types)` w `serialization/message_registry.py` oraz `build_command_registry(command_types)` w `serialization/command_registry.py` — analogiczne otoczki.

## Kluczowe pliki

- `shell/platform/infrastructure/messaging/inbox/envelope_validator.py`
- `shell/platform/infrastructure/serialization/upcaster.py`
- `shell/platform/infrastructure/serialization/event_deserializer.py`
- `shell/platform/infrastructure/serialization/event_serializer.py`
- `shell/platform/infrastructure/serialization/message_deserializer.py`
- `shell/platform/infrastructure/serialization/message_serializer.py`
- `shell/platform/infrastructure/messaging/serialization/command_deserializer.py`
- `shell/platform/infrastructure/serialization/type_registry.py`
- `shell/platform/infrastructure/serialization/event_registry.py`
- `shell/platform/infrastructure/serialization/message_registry.py`
- `shell/platform/infrastructure/serialization/command_registry.py`

## Powiązane koncepcje

- [delivery-transport](delivery-transport.md)
- [contract-catalog](contract-catalog.md)
- [integration-contracts](integration-contracts.md)
- [delivery-overview](delivery-overview.md)
- [inbox-processor](inbox-processor.md)
