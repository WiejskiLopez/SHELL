# Obsługa błędów — DomainError, ProblemDetail (RFC 7807), globalne wyjątki

## Cel / Co realizuje

Warstwa obsługi błędów mapuje wyjątki aplikacji na odpowiedzi HTTP w spójnym,
maszynowo czytelnym formacie `ProblemDetail` (RFC 7807). Błędy domenowe
(`DomainError`) i ich specjalizacje (np. `ConcurrentModificationError`) są
tłumaczone na statusy HTTP 400/409, błędy walidacji FastAPI na 422 z listą pól,
a nieprzewidziane wyjątki na ustrukturyzowane 500. Rejestracja handlerów odbywa
się centralnie w `setup_api_common` oraz per-BC w fabrykach aplikacji.

## Problem

Rzucanie surowych wyjątków przez handler/agregat daje domyślne, nieinformacyjne
odpowiedzi 500 i niespójny kształt błędów między endpointami. Klient potrzebuje
jednolitego kontraktu błędu: `title`, `status`, `detail`, `instance`,
`correlation_id`, `timestamp`, opcjonalnie listy `errors` dla walidacji.
Jednocześnie błędy o znanym znaczeniu biznesowym (naruszony invariant, konflikt
współbieżności) muszą mapować się na właściwe statusy HTTP bez ujawniania
wewnętrznych szczegółów.

## Realizacja techniczna

### ProblemDetail — `shell/platform/framework/api/models/problem_detail.py`

`ProblemDetail(BaseModel)` — pola: `type` (domyślnie `"about:blank"`), `title`,
`status`, `detail`, `instance` (opcjonalne), `errors` (lista `FieldError`),
`correlation_id` (opcjonalne), `timestamp` (ISO 8601). Statyczna metoda
`ProblemDetail.now_iso()` generuje znacznik czasu w UTC.

`FieldError(BaseModel)` — pojedynczy błąd walidacji: `field`, `message`,
`code` (opcjonalne), `value` (opcjonalne).

### Handlery — `shell/platform/framework/api/middleware/error_handler.py`

- `domain_error_handler(request, exc: DomainError)`:
  - `isinstance(exc, ConcurrentModificationError)` → `409` z `{"detail": str(exc)}`;
  - w przeciwnym razie → `400` z `{"detail": str(exc)}`.
- `application_error_handler(request, exc: ApplicationError)` → `400`
  z `{"detail": str(exc)}` (handler zdefiniowany, rejestrowany per-BC).
- `http_exception_handler(request, exc: HTTPException)` → `ProblemDetail`
  z `title` i `detail` równymi `exc.detail`, `status=exc.status_code`,
  `timestamp=ProblemDetail.now_iso()`.
- `validation_error_handler(request, exc: RequestValidationError)` → `422`
  z `ProblemDetail` (title "Validation Error") i listą `errors`; każde
  `FieldError` budowane z wpisu `exc.errors()`: `field` = loc połączone kropką,
  `message` = msg, `code` = type.
- `unhandled_exception_handler(request, exc: Exception)` → `500` z
  `ProblemDetail` (title "Internal Server Error", genericzny `detail` — nie
  ujawnia treści wyjątku).

### Rejestracja

`_register_error_handlers` (`shell/platform/framework/api/setup.py`) rejestruje:

```python
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(DomainError, domain_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
```

BC mogą rozszerzać mapowanie: `create_execution_app` dodaje własny
`app.add_exception_handler(DomainError, domain_error_handler)`
(`shell/execution_service/framework/execution/api/app.py`). Dodatkowe mapowania
specyficzne dla BC mają być dodawane per-BC (komentarz w module
`error_handler.py`).

### Hierarchia wyjątków

- `DomainError(Exception)` — `shell/platform/domain/exceptions/domain_error.py`,
  baza dla naruszonych reguł/invariantów domeny.
- `ConcurrentModificationError(DomainError)` —
  `shell/platform/domain/exceptions/concurrent_modification_error.py`,
  konstruktor `(aggregate_name, aggregate_id)` → komunikat
  `"{aggregate_name} was concurrently modified: id={aggregate_id!r}"`; mapowany na 409.
- `ApplicationError` — `shell/platform/application/exceptions/`, mapowany na 400.

## Kluczowe pliki

- `shell/platform/framework/api/models/problem_detail.py`
- `shell/platform/framework/api/middleware/error_handler.py`
- `shell/platform/framework/api/setup.py`
- `shell/platform/domain/exceptions/domain_error.py`
- `shell/platform/domain/exceptions/concurrent_modification_error.py`
- `shell/platform/application/exceptions/`

## Powiązane koncepcje

- [http-api](http-api.md)
- [api-middleware](api-middleware.md)
- [domain-errors](domain-errors.md)
- [tracing-context](tracing-context.md)
