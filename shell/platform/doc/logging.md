# Logowanie i audyt

## Cel / Co realizuje

Logowanie w SHELL opiera się na portcie `Logger` (`shell/platform/application/ports/logger.py`), którego podstawową implementacją jest `StdlibLogger` (`shell/platform/infrastructure/logging/stdlib_logger/stdlib_logger.py`) z formatowaniem JSON przez `JsonFormatter`. Konfigurację root loggera wykonuje `setup_logging()` (`shell/platform/bootstrap/logging/setup_logging.py`). Osobno istnieje adapter `LoggingEventPublisher` (każdy domain event jako wpis logu). Trwały audyt zdarzeń (tabela `audit_event`) jest zapisywany atomowo z wierszem outboxu w `SqlAlchemyUnitOfWorkBase._write_staged_outbox()` — patrz [transactional-outbox](transactional-outbox.md).

## Problem

W systemie rozproszonym dzienniki muszą być maszynowo parsowalne i skorelowane (correlation_id) — goły tekst wielolinijkowy nie nadaje się do agregacji. Jednocześnie eventy domenowe są cennym źródłem audytu, ale ich trwała rejestracja nie może zależeć od publikowania do brokera. Potrzebny jest: jeden spójny format logu, konfiguracja dostępna w każdym entrypoincie oraz trwały audyt zdarzeń (zapis w tej samej transakcji co outbox).

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

### Trwały audyt — `audit_event`

Tabela `audit_event` (model `build_audit_event_model`, kolumny `id`, `integration_event_name`, `occurred_at`, `payload`) jest zapisywana **atomowo z wierszem outboxu** w `SqlAlchemyUnitOfWorkBase._write_staged_outbox()`:

```python
self._session.add(
    self._models.audit(
        id=self._id_generator.new_id(),
        integration_event_name=envelope["contract_type"],
        occurred_at=envelope["occurred_at"],
        payload=envelope["payload"],
    )
)
```

Zapis audytu jest częścią tej samej transakcji co zmiana domenowa i outbox — nie istnieje osobny adapter `SqlAuditPublisher`; nic nie pisze do `audit_event` poza UoW.

## Kluczowe pliki

- `shell/platform/infrastructure/logging/stdlib_logger/stdlib_logger.py`
- `shell/platform/infrastructure/logging/stdlib_logger/json_formatter.py`
- `shell/platform/bootstrap/logging/setup_logging.py`
- `shell/platform/infrastructure/logging/logging_event_publisher.py`
- `shell/platform/infrastructure/persistence/sql/models/audit_delivery.py`
- `shell/platform/infrastructure/persistence/sql_alchemy_uow_base.py`
- `shell/platform/application/ports/logger.py` (port `Logger`)

## Powiązane koncepcje

- [tracing-context](tracing-context.md)
- [domain-event](domain-event.md)
- [transactional-outbox](transactional-outbox.md)
- [sqlalchemy-persistence](sqlalchemy-persistence.md)
- [configuration](configuration.md)
- [delivery-models](delivery-models.md)