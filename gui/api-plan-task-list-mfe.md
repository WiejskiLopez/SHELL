# Task List MFE — plan API

## Opis
Mikrofrontend lewej kolumny (22% szerokości). Wyświetla listę zadań (task executions) dla wybranego workflow. Pozwala tworzyć nowe zadania i wybierać aktywne zadanie.

---

## 1. Wymagane endpointy

### `GET /api/v1/task-executions`
Lista tasków dla wybranego workflow.

- Query params: `page`, `page_size`, `workflow_id` (wymagany)
- Response (200):
  ```json
  {
    "items": [
      {
        "id": "string",
        "name": "string",
        "work_dir": "string",
        "workflow_id": "string",
        "status": "string",
        "created_at": "datetime",
        "updated_at": "datetime | null"
      }
    ],
    "total": 0,
    "page": 1,
    "page_size": 20,
    "has_more": false
  }
  ```

### `POST /api/v1/task-executions/`
Utworzenie nowego taska (np. gdy użytkownik pierwszy raz wysyła komendę).

- Request Body:
  ```json
  {
    "workflow_id": "string",
    "name": "string"
  }
  ```
- Response (201):
  ```json
  {
    "id": "string"
  }
  ```

### `GET /api/v1/task-executions/{id}`
Pobranie szczegółów pojedynczego taska (do odświeżenia po kliknięciu).

- Response (200):
  ```json
  {
    "id": "string",
    "name": "string",
    "work_dir": "string",
    "workflow_id": "string",
    "status": "string",
    "created_at": "datetime",
    "updated_at": "datetime | null",
    "deleted_at": "datetime | null"
  }
  ```

### `GET /api/v1/workflows/{workflow_id}` (opcjonalnie)
Pobranie nagłówka workflow dla lewej kolumny.

- Odwołanie do Header MFE — ten sam endpoint.

---

## 2. Stan backendu

| Endpoint | Status | Uwagi |
|---|---|---|
| `GET /api/v1/task-executions` | ⚠️ Częściowo | Istnieje, ale brak filtra `?workflow_id=`. Zwraca wszystkie tas̨ki. |
| `GET /api/v1/task-executions/{id}` | ✗ Brak | Endpoint nie istnieje w routerze. |
| `POST /api/v1/task-executions/` | ✗ Brak | Nie istnieje. |
| `Domain TaskExecution` | ✓ Jest | Agregat istnieje z pełnym lifecyclem (CREATED → IN_PROGRESS → COMPLETED/FAILED). |
| `TaskExecutionResponse` | ✓ Jest | Model istnieje, ale brak w nim `status`. |

## 3. Co trzeba zbudować / zmienić w backendzie

### Priorytet 1 — filtry
- [ ] Dodać filtr `?workflow_id=` do `GET /api/v1/task-executions`
- [ ] Rozszerzyć `ListTaskExecutionsQuery` o `workflow_id`
- [ ] Dodać filtr w `TaskExecutionQueryService.list_all()`

### Priorytet 2 — brakujące endpointy
- [ ] Dodać `GET /api/v1/task-executions/{id}` (get by id)
- [ ] Dodać `POST /api/v1/task-executions/` (create)
- [ ] Stworzyć `CreateTaskExecutionCommand` + handler + controller

### Priorytet 3 — model
- [ ] Dodać `status` do `TaskExecutionResponse` (DTO ma status, response go nie wystawia)
- [ ] Upewnić się że `TaskExecutionResponse` zawiera wszystkie wymagane pola

---

## 4. Uwagi

- TaskExecution ma już w domenie status lifecycle: `CREATED → IN_PROGRESS → COMPLETED | FAILED | TIMED_OUT | EXHAUSTED`
- W przyszłości: WebSocket do powiadamiania o zmianie statusu taska w czasie rzeczywistym
- Gdy task jest aktywny, karta w lewej kolumnie ma podświetlenie (`(Aktywny)`)
