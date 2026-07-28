# Auth MFE — plan API

## Opis
Mikrofrontend odpowiedzialny za logowanie użytkownika. Używa uproszczonego flow: user podaje email → backend znajduje usera → zwraca jego ID. Brak haseł, brak tokenów (MVP).

---

## 1. Wymagane endpointy

### `GET /api/v1/users/by-email?email=...`
Pobranie ID użytkownika po emailu.

- Query param: `email` (wymagany)
- Response (200):
  ```json
  {
    "id": "string"
  }
  ```
- Response (404): użytkownik o podanym emailu nie istnieje

Frontend przechowuje `id` w pamięci / localStorage i wysyła w kolejnych requestach.

---

## 2. Stan backendu (po implementacji)

| Endpoint | Status |
|---|---|
| `GET /api/v1/users/by-email?email=...` | ✓ Zaimplementowane |
| `GET /api/v1/users/{id}` | ✓ Istnieje (do pobrania profilu po ID) |

## 3. Co jeszcze może być potrzebne

- W przyszłości: obsługa `X-User-Id` w AuthMiddleware jeśli chcemy identyfikować usera w pozostałych endpointach
- Rejestracja na razie przez istniejący `POST /api/v1/users/`
