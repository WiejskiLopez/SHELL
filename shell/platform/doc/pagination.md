# Paginacja — Page (strony, limit/offset, meta odpowiedzi)

## Cel / Co realizuje

Platforma definiuje jeden generyczny kontener odpowiedzi listowych — `Page[T]`
(`shell/platform/framework/api/models/page.py`) — używany jako `response_model`
w endpointach listowych wszystkich BC. Kontener niesie elementy (`items`) oraz
meta-dane paginacji: `total`, `page`, `page_size`, `has_more`. Konwencja
paginacji oparta jest o numer strony i rozmiar strony (page/page_size),
przeliczane na `offset`/`limit` w zapytaniach SQL, a flagę `has_more` liczy
kontroler z `total`.

## Problem

Listowe endpointy (użytkownicy, projekty, sesje, workflowy, task executions)
muszą zwracać powtarzalny, przewidywalny kształt odpowiedzi z informacją o
całkowitej liczbie rekordów i możliwości kontynuacji. Bez wspólnego kontenera
każdy BC definiowałby własny kształt meta-danych, a klienci API nie mieliby
gwarancji co do nazw pól. Kontener jest też wstrzykiwany do schematów OpenAPI
przez `_inject_common_schemas`.

## Realizacja techniczna

### Model — `shell/platform/framework/api/models/page.py`

```python
T = TypeVar("T")

class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    has_more: bool
```

`Page` to `pydantic.BaseModel` z generycznym parametrem `T` (typ elementów,
np. `Page[UserResponse]`), frozen nie jest wymagany — odpowiedź budowana jest
przez kontroler i serializowana przez FastAPI.

### Parametry zapytania (router)

Routery listowe deklarują parametry przez `fastapi.Query` z aliasem `page_size`:

```python
page: int = Query(default=1, ge=1),
page_size: int = Query(default=100, ge=1, le=1000, alias="page_size"),
```

przy `response_model=Page[UserResponse]` / `Page[ProjectResponse]` /
`Page[SessionResponse]` / `Page[WorkflowResponse]` / `Page[TaskExecutionResponse]`
(np. `shell/user_service/framework/user/user/api/router.py`,
`shell/execution_service/framework/execution/workflow/api/router.py`).

### Przepływ danych

1. **Router** przekazuje `page`/`page_size` do kontrolera.
2. **Kontroler** buduje komendę/zapytanie CQRS, np.
   `ListUsersQuery(page=page, page_size=page_size)`, i wysyła przez
   `query_bus.dispatch(...)`.
3. **Query handler** deleguje do portu query service, np.
   `list_all(page=..., page_size=...)`.
4. **Query service (SQL)** liczy `offset = (page - 1) * page_size` i stosuje
   `.offset(offset).limit(page_size)` na zapytaniu (np.
   `user_query_service.py`, `project_query_service.py`,
   `workflow_query_service.py`); zwraca krotkę `(lista DTO, total)`.
5. **Kontroler** mapuje DTO na odpowiedź API i liczy:

```python
has_more = (page * page_size) < total
return Page(
    items=items,
    total=total,
    page=page,
    page_size=page_size,
    has_more=has_more,
)
```

przykład: `shell/user_service/framework/user/user/api/controller.py` (`list_users`),
`shell/project_service/framework/project/project/api/controller.py` (`list_projects`),
`shell/session_service/framework/session/session/api/controller.py` (`list_sessions`),
`shell/execution_service/framework/execution/workflow/api/controller.py`
(`list_workflows`).

### Semantyka `has_more`

`has_more = (page * page_size) < total` — prawda, gdy na bieżącej stronie
prawdopodobnie nie mieszczą się wszystkie rekordy (offset bieżącej strony
< `total`). Testy e2e (`shell/tests/platform/e2e/api/test_pagination.py`)
weryfikują m.in. `page_size=100` oraz `has_more` przy `page=1`/`page=3` dla
`page_size=2`.

## Kluczowe pliki

- `shell/platform/framework/api/models/page.py`
- `shell/user_service/framework/user/user/api/controller.py`
- `shell/user_service/framework/user/user/api/router.py`
- `shell/project_service/framework/project/project/api/controller.py`
- `shell/session_service/framework/session/session/api/controller.py`
- `shell/execution_service/framework/execution/workflow/api/controller.py`

## Powiązane koncepcje

- [http-api](http-api.md)
- [cqrs-buses](cqrs-buses.md)
- [error-handling](error-handling.md)
