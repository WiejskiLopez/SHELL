# Logowanie i audyt

## Cel / Co realizuje

Logowanie w SHELL opiera się na portcie `Logger` (`shell/platform/application/ports/ports.py`), którego podstawową implementacją jest `StdlibLogger` (`shell/platform/infrastructure/logging/stdlib_logger/stdlib_logger.py`) z formatowaniem JSON przez `JsonFormatter`. Konfigurację root loggera wykonuje `setup_logging()` (`shell/platform/bootstrap/logging/setup_logging.py`). Osobno istnieją dwa adaptery EventPublisher: `LoggingEventPublisher` (każdy domain event jako wpis logu) i `SqlAuditPublisher` (każdy domain event jako wiersz w tabeli `audit_event`).

## Problem

W systemie rozproszonym dzienniki muszą być maszynowo parsowalne i skorelowane (correlation_id) — goły tekst wielolinijkowy nie nadaje się do agregacji. Jednocześnie eventy domenowe są cennym źródłem audytu, ale ich trwała rejestracja nie może zależeć od publikowania do brokera. Potrzebny jest: jeden spójny format logu, konfiguracja dostępna w każdym entrypoincie oraz dwa komplementarne mechanizmy publikacji eventów (log + baza).

## Realizacja techniczna

### `StdlibLogger`

Implementuje port `Logger` opakowując `logging.getLogger(name)` (domyślnie `"shell"`, level `logging.INFO`). Metody `debug/info/warning/error(msg, **kw)` przekazują `kw` jako `extra` do `LogRecord`. Dzięki temu dowolne pola strukturalne (np. `event_type=...`) trafiają do rekordu i mogą być sformatowane przez `JsonFormatter`.

### `JsonFormatter`

`JsonFormatter(logging.Formatter)` (w `json_formatter.py`) zamienia rekord na pojedynczą linię JSON:

- stałe pola: `ts` (ISO8601 UTC przez `datetime.now(tz=UTC).isoformat()`), `level`, `logger` (nazwa loggera), `msg` (`record.getMessage()`), `correlation_id` (z `shell/platform/infrastructure/context.get_correlation_id()` — patrz [tracing-context](tracing-context.md));
- `exc_info` dołączane, gdy rekord zawiera wyjątek;
- pozostałe atrybuty rekordu spoza zbioru `_std_keys` (klucze standardowych atrybutów `LogRecord` + `message`, `asctime`, `TaskExecutionName`) i nie zaczynające się od `_` trafiają do `extra` (dict);
- `json.dumps(data, default=str)` — wartości nieserializowalne konwertowane przez `str`.

### `setup_logging()`

`shell/platform/bootstrap/logging/setup_logging.py` konfiguruje root logger globalnie: `StreamHandler(sys.stdout)` z `JsonFormatter()`, `basicConfig(level=logging.INFO, handlers=[handler], force=True)`. `force=True` nadpisuje każdą wcześniejszą konfigurację, gwarantując jednolity format we wszystkich procesach (workers, CLI, API).

### `LoggingEventPublisher`

Adapter `EventPublisher` (`publish(events: Sequence[object])`) logujący każdy domain event jako `logger.info("domain_event", event_type=type(event).__name__, occurred_at=event.occurred_at.value.isoformat())`. Służy jako obserwowalność eventów w środowiskach bez brokerów oraz przy testach.

### `SqlAuditPublisher`

Adapter `EventPublisher` zapisujący audyt do bazy. Konstruktor przyjmuje `session_factory: async_sessionmaker[AsyncSession]` oraz `models: PersistenceDeliveryModels` (wykorzystuje `models.audit` — model z `build_audit_event_model`). `publish()`:

1. `DomainEventSerializer().to_payload(event)` (z `shell/platform/infrastructure/serialization`) serializuje event do payloadu;
2. tworzy wiersz `audit_model(id=str(uuid.uuid4()), event_type=type(event).__name__, occurred_at=event.occurred_at.value, payload=payload)`;
3. błąd serializacji → `logging.getLogger(__name__).critical("Failed to serialize audit event %s — event LOST", ...)` i `raise` (nie ma cichych upadków);
4. pojedynczy `await session.commit()` dla całej partii.

## Kluczowe pliki

- `shell/platform/infrastructure/logging/stdlib_logger/stdlib_logger.py`
- `shell/platform/infrastructure/logging/stdlib_logger/json_formatter.py`
- `shell/platform/bootstrap/logging/setup_logging.py`
- `shell/platform/infrastructure/logging/logging_event_publisher.py`
- `shell/platform/infrastructure/logging/sql_audit_publisher.py`
- `shell/platform/application/ports/ports.py` (port `Logger`)

## Powiązane koncepcje

- [tracing-context](tracing-context.md)
- [domain-event](domain-event.md)
- [sqlalchemy-persistence](sqlalchemy-persistence.md)
- [configuration](configuration.md)
- [delivery-models](delivery-models.md)
