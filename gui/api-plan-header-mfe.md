# Header MFE — plan API

## Opis
Mikrofrontend górnej belki — wybór sesji (lewa strona), pasek workflowów (środek), profil użytkownika (prawa strona). Widoczny tylko dla zalogowanego użytkownika.

---

## 1. Wymagane endpointy

### `GET /api/v1/sessions`
Lista wszystkich sesji do wyboru w dropdownie.

- Query params: `page`, `page_size`
- Response (200):
  ```json
  {
    "items": [
      {
        "id": "string",
        "goal": "string",
        "status": "string",
        "opened_at": "datetime",
        "closed_at": "datetime | null",
        "created_at": "datetime"
      }
    ],
    "total": 0,
    "page": 1,
    "page_size": 20,
    "has_more": false
  }
  ```

### `GET /api/v1/workflows`
Lista workflowów dla wybranej sesji (do wyświetlenia jako zakładki w headerze).

- Query params: `page`, `page_size`, `session_id` (wymagany dla filtra)
- Response (200):
  ```json
  {
    "items": [
      {
        "id": "string",
        "status": "string",
        "session_id": "string",
        "created_at": "datetime"
      }
    ],
    "total": 0,
    "page": 1,
    "page_size": 20,
    "has_more": false
  }
  ```

### `POST /api/v1/sessions/`
Utworzenie nowej sesji (gdy user chce rozpocząć nową sesję).

- Request Body:
  ```json
  {
    "goal": "string"
  }
  ```
- Response (201):
  ```json
  {
    "id": "string"
  }
  ```

### `POST /api/v1/workflows/`
Utworzenie nowego workflow w ramach sesji.

- Request Body:
  ```json
  {
    "session_id": "string"
  }
  ```
- Response (201):
  ```json
  {
    "id": "string"
  }
  ```

### `GET /auth/me`
Pobranie profilu użytkownika (do wyświetlenia awatara i nazwy w prawym górnym rogu).

- Odwołanie do Auth MFE — ten sam endpoint co w `api-plan-auth-mfe.md`

---

## 2. Stan backendu

| Endpoint | Status | Uwagi |
|---|---|---|
| `GET /api/v1/sessions` | ✓ Jest | Paginowana lista sesji z opcjonalnym filtrem `user_id`. |
| `GET /api/v1/sessions/{id}` | ✓ Jest | Zwraca SessionResponse. |
| `POST /api/v1/sessions/` | ✓ Jest | Tworzy sesję z `goal`. |
| `GET /api/v1/workflows` | ✓ Jest (częściowo) | Endpoint istnieje, ale nie ma filtra `?session_id=`. |
| `GET /api/v1/workflows/{id}` | ✓ Jest | Zwraca WorkflowResponse. |
| `POST /api/v1/workflows/` | ✓ Jest | Tworzy workflow z `session_id`. |
| `GET /auth/me` | ✗ Brak | Zależne od endpointu auth. |

## 3. Co trzeba zbudować / zmienić w backendzie

### Priorytet — zależności wstępne
- [ ] Auth MFE musi być gotowe (login, `GET /auth/me`)

### Priorytet — sesje
- [x] Dodać `GET /api/v1/sessions` (list sessions) z paginacją i filtrem `user_id`
- [ ] Dodać opcjonalny filtr `?status=` do listowania sesji

### Priorytet — workflowy
- [ ] Dodać filtr `?session_id=` do `GET /api/v1/workflows`
- [ ] Dodać opcjonalny filtr `?status=` (już jest)

---

## 4. Uwagi

- Obecnie `ListWorkflowsQuery` przyjmuje tylko `page`, `page_size`, `status`. Trzeba dodać `session_id` do query, handlera i SQL.
- `GET /api/v1/sessions` (list) wymaga dodania nowego query: `ListSessionsQuery` + handler + endpoint.
- Header MFE nie potrzebuje mutacji poza tworzeniem — cała reszta to odczyt.
