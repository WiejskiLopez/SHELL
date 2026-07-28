# Schemat przepływu — zależności między MFE a backendem

```
┌─────────────────────────────────────────────────────────────────────────┐
│  AGENT_OS Dashboard                                                     │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ HEADER MFE (górna belka)                                          │  │
│  │ [ Sesja ▼ ] [ Workflow #001 ▼ ] [ Workflow #002 ]    [ 👤 Jan K. ]│  │
│  └───────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────┐ ┌──────────────────────────┐ ┌──────────────────┐    │
│  │ TASK LIST    │ │ TASK CONTEXT             │ │ RESERVED         │    │
│  │ MFE (22%)    │ │ MFE (56%)                │ │ MFE (22%)        │    │
│  │              │ │ ┌────────────────────┐   │ │                  │    │
│  │ WORKFLOW #001│ │ │ Agent Status       │   │ │ [Miejsce         │    │
│  │              │ │ │ [T-102] Agent... ○ │   │ │  rezerwowane]    │    │
│  │ [+ Add Task] │ │ └────────────────────┘   │ │                  │    │
│  │              │ │ ┌────────────────────┐   │ │                  │    │
│  │ ┌──────────┐ │ │ │ Execution Logs     │   │ │                  │    │
│  │ │T-102 API │ │ │ │ [Agent] ...        │   │ │                  │    │
│  │ │(Aktywny) │ │ │ │ [System] ...       │   │ │                  │    │
│  │ └──────────┘ │ │ │ [User] ...         │   │ │                  │    │
│  │              │ │ └────────────────────┘   │ │                  │    │
│  │ T-101 Raport │ │ ┌────────────────────┐   │ │                  │    │
│  │              │ │ │ User Input         │   │ │                  │    │
│  │              │ │ │ [_______________]  │   │ │                  │    │
│  │              │ │ │ [ Wyślij ✈ ]      │   │ │                  │    │
│  │              │ │ └────────────────────┘   │ │                  │    │
│  └──────────────┘ └──────────────────────────┘ └──────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

## Kolejność implementacji

### Faza 1 — Auth MFE (bloker dla reszty)
Endpointy do zbudowania:
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `POST /auth/logout`

Frontend: ekran logowania. Bez tego user nic nie widzi.

### Faza 2 — Header MFE (sesje + workflowy + profil)
Endpointy do zbudowania:
- `GET /api/v1/sessions` (list) — ✗ nowy
- `GET /api/v1/workflows?session_id=...` — ✗ dodać filtr
- `GET /auth/me` — z fazy 1

Frontend: górna belka z wyborem sesji i zakładkami workflowów.

### Faza 3 — Task List MFE (lewa kolumna)
Endpointy do zbudowania:
- `GET /api/v1/task-executions?workflow_id=...` — ✗ dodać filtr
- `GET /api/v1/task-executions/{id}` — ✗ nowy
- `POST /api/v1/task-executions/` — ✗ nowy

Frontend: lista tasków + wybór aktywnego.

### Faza 4 — Task Context MFE (środkowa kolumna — chat)
Endpointy do zbudowania:
- `POST /api/v1/chat/messages` — ✗ nowy (cały chat domain)
- `GET /api/v1/chat/messages?task_execution_id=...` — ✗ nowy
- WebSocket `/ws/session/{session_id}` — ✗ zarejestrować istniejący handler
- `GET /api/v1/node-executions/{id}/result` — ✓ już jest

Frontend: czat z agentem, status agenta, wysyłanie komend.

### Faza 5 — Reserved MFE (prawa kolumna)
Endpoty do zbudowania: przyszłość.

---

## Zależności między fazami

```
Faza 1 (Auth)
    │
    ▼
Faza 2 (Header) ← potrzebuje GET /auth/me (z fazy 1)
    │
    ▼
Faza 3 (Task List) ← potrzebuje GET /workflows (z fazy 2)
    │
    ▼
Faza 4 (Task Context) ← potrzebuje GET /task-executions (z fazy 3)
    │
    ▼
Faza 5 (Reserved) ← niezależne
```

Każda faza może być implementowana iteracyjnie: najpierw backend, potem frontend.
