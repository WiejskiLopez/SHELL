# Task Context MFE — plan API

## Opis
Mikrofrontend środkowej kolumny (56% szerokości). Trzy sekcje: Status Agenta (góra), Historia Komunikacji / logi (środek), Wprowadzanie Poleceń (dół). Główna przestrzeń pracy.

---

## 1. Wymagane endpointy

### `POST /api/v1/chat/messages`
Wysłanie wiadomości użytkownika do agenta. Główny endpoint interakcji.

- Request Body:
  ```json
  {
    "task_execution_id": "string",
    "content": "string"
  }
  ```
- Response (202 — Accepted):
  ```json
  {
    "message_id": "string",
    "status": "accepted"
  }
  ```
- Odpowiedź przychodzi asynchronicznie przez WebSocket/SSE (patrz niżej).

### `GET /api/v1/chat/messages`
Pobranie historii konwersacji dla danego taska.

- Query params: `task_execution_id` (wymagany), `page`, `page_size`
- Response (200):
  ```json
  {
    "items": [
      {
        "id": "string",
        "task_execution_id": "string",
        "role": "user | agent | system",
        "content": "string",
        "created_at": "datetime"
      }
    ],
    "total": 0,
    "page": 1,
    "page_size": 50,
    "has_more": false
  }
  ```

### `GET /api/v1/node-executions/{id}/result`
Pobranie rezultatu wykonania noda (status agenta).

- Query params: `workflow_id` (wymagany)
- Response (200):
  ```json
  {
    "node_execution_id": "string",
    "workflow_id": "string",
    "status": "string",
    "stdout": "string | null",
    "stderr": "string | null",
    "artifact_uri": "string | null",
    "created_at": "string | null"
  }
  ```

### WebSocket `/ws/session/{session_id}`
Strumieniowanie odpowiedzi agenta i logów systemowych w czasie rzeczywistym.

- Po połączeniu klient otrzymuje zdarzenia:
  ```json
  {
    "type": "agent_message" | "system_log" | "status_change",
    "task_execution_id": "string",
    "content": "string",
    "timestamp": "datetime"
  }
  ```

### SSE `/api/v1/chat/stream?task_execution_id=...`
Alternatywny kanał do streamowania odpowiedzi agenta (prostszy niż WebSocket).

- `text/event-stream` z eventami:
  ```
  event: message
  data: {"role": "agent", "content": "...", "timestamp": "..."}

  event: log
  data: {"content": "...", "timestamp": "..."}

  event: status
  data: {"status": "running|completed|failed", "timestamp": "..."}

  event: done
  data: {}
  ```

---

## 2. Stan backendu

| Endpoint | Status | Uwagi |
|---|---|---|
| `POST /api/v1/chat/messages` | ✗ Brak | Całkowicie nie istnieje. Nie ma koncepcji "chatu" w API. |
| `GET /api/v1/chat/messages` | ✗ Brak | Nie istnieje. |
| `GET /api/v1/node-executions/{id}/result` | ✓ Jest | Zwraca NodeExecutionResultResponse. |
| WebSocket `/ws/session/{session_id}` | ⚠️ Handler istnieje | `SessionWebSocketHandler` istnieje w `ws/session_ws.py` ale NIE jest zarejestrowany jako route FastAPI. |
| SSE `/api/v1/chat/stream` | ✗ Brak | Nie istnieje. |

## 3. Co trzeba zbudować w backendzie

### Priorytet 1 — Chat domain
- [ ] Stworzyć agregat `Message` / `ChatMessage` (role, content, task_execution_id, timestamp)
- [ ] Stworzyć `ChatMessageResponse` DTO
- [ ] Stworzyć repozytorium i mapper dla wiadomości

### Priorytet 2 — Endpointy chatu
- [ ] `POST /api/v1/chat/messages` — przyjmuje komendę, zapisuje wiadomość usera, triggeruje agenta
- [ ] `GET /api/v1/chat/messages?task_execution_id=...` — zwraca historię konwersacji

### Priorytet 3 — Streaming
- [ ] Zarejestrować WebSocket handler jako route w FastAPI
- [ ] Lub stworzyć SSE endpoint `/api/v1/chat/stream`
- [ ] Podpiąć broadcast zdarzeń z backendu (gdy agent produkuje output, wysłać przez WS/SSE)

---

## 4. Uwagi

- To jest największa luka między backendem a frontendem. Backend nie ma w ogóle koncepcji czatu ani interakcji user↔agent.
- `MessageRouter` istnieje ale służy do routowania wiadomości między komponentami systemu — to nie to samo co chat.
- Na początek można zrobić prosty model: wiadomość usera → triggeruje wykonanie → zwraca response przez polling. WebSocket/SSE mogą być później.
- Agent Status MFE używa `GET /api/v1/node-executions/{id}/result` — ten endpoint już istnieje.
- Historia komunikacji (Execution Logs MFE) i User Input MFE dzielą te same endpointy czatu.
