# Enterprise Auth Refactor

## Cel

Uporzadkowac obecny email-only login w oparciu o istniejacy agregat `User` i nowy agregat `AuthSession`.

```text
User        1--N AuthSession
User        1--N dane domenowe
```
`User.email` pozostaje zrodlem prawdy dla emaila biznesowego i loginu. `AuthSession` przechowuje cykl zycia sesji logowania. Nie tworzymy osobnego agregatu identity.

## Kontrakt API

Base path: `/api/v1`

### POST `/auth_session/login`

Request:

```json
{
  "email": "user@example.com"
}
```

Response `200` zwraca **tylko identyfikator sesji** — spójnie z konwencja aplikacji, gdzie kazdy POST tworzacy zasob zwraca `{id}`. Backend ustanawia sesje i ustawia bezpieczne cookies.

```json
{
  "id": "auth-session-id"
}
```

Bledny lub nieaktywny email: `401` z generycznym komunikatem.

Token nie jest zwracany w JSON — leci wylacznie do `HttpOnly` cookie. `user_id` nie jest zwracany przez login; frontend pozyskuje go z `GET /auth_session/me`.

Techniczny przebieg:

```text
1. Frontend wysyla POST /api/v1/auth_session/login z emailem.
2. Router przekazuje request do kontrolera AuthSession.
3. Kontroler tworzy `LoginAuthSessionCommand` i wysyla go przez `CommandBus`.
4. `LoginAuthSessionHandler` odczytuje `User` po `User.email` (QueryService) i sprawdza `User.status`.
5. Brak `User` lub nieaktywny: `401`, bez tworzenia sesji.
6. Dla aktywnego `User` handler robi get-or-create: szuka aktywnej `AuthSession` po `user_id`
   (repozytorium `get_active_by_user_id(user_id, now)`); nie ma -> tworzy nowa z losowym tokenem
   i hashem; jest -> zwraca istniejaca (bez duplikowania).
7. Handler zapisuje tylko `AuthSession` z `user_id`, hashem tokena i `expires_at`.
8. Kontroler ustawia raw token w `HttpOnly` cookie.
9. Odpowiedz zwraca tylko `AuthSession.id`.
```

Token jawny nie jest zapisywany w bazie ani zwracany w JSON (w bazie tylko SHA-256 hash). Handler nie modyfikuje `User` — tylko go czyta.

### GET `/auth_session/me`

Czyta cookie, rozpoznaje `AuthSession` po `token_hash` i zwraca dane identyfikujace zalogowanego usera:

```json
{
  "user_id": "user-id"
}
```

Brak lub niewazna (revoked/expired/deleted) sesja: `401`.

### POST `/auth_session/logout`

Revokuje biezaca `AuthSession`, czysci cookies i jest idempotentny. Odpowiedz: `204`.

## Backend

### Agregat `User`

Istniejacy `shell/domain/user/aggregates/user/user.py` pozostaje agregatem biznesowym i zrodlem danych logowania.

Obecne `User.email` pozostaje:

1. canonical login identifier oraz dane kontaktowe uzywane przez domene;
2. polem zarzadzanym przez `User`, z walidacja i unikalnoscia;
3. jedynym miejscem, z ktorego login pobiera email;
4. wartoscia zwracana w publicznym widoku usera (gdy frontend go pobierze).

Zmiana emaila aktualizuje tylko agregat `User`.

### Agregat `AuthSession`

Lokalizacja: `shell/domain/user/aggregates/auth_session/` — **zaimplementowany**.

Wlasciciel:

- `auth_session_id`;
- `user_id` jako wymagany foreign key do `User` — uzywa `UserId` z user BC (nie `UserIdRef`, ktory jest referencja miedzy BC);
- hash tokena sesji (SHA-256), nigdy raw token;
- `created_at`;
- `expires_at`;
- `revoked_at`;

Struktura domenowa:

- `auth_session.py` — agregat `AuthSession` dziedziczacy po `AggregateRoot[AuthSessionId]`; metody domenowe `create`/`restore`/`update`/`delete`/`revoke` z guard clause + `append_event()`; slot ordering zgodny ze standardem.
- `value_objects/auth_session_id.py` — `AuthSessionId(EntityId)`.
- `events/` — `AuthSessionCreatedEvent`, `AuthSessionUpdatedEvent`, `AuthSessionRevokedEvent`, `AuthSessionDeletedEvent`.
- `repositories/auth_session_repository.py` — port `AuthSessionRepository` (Protocol).

Nie uzywac istniejacego `Session`, poniewaz `shell/domain/session/aggregates/session/session.py` jest sesja workflowu `OPEN/CLOSED`.

### Warstwa aplikacyjna i infrastruktura

Zaimplementowane:

- agregat `AuthSession` w `shell/domain/user/aggregates/auth_session/`;
- port repozytorium `AuthSessionRepository` przy agregacie;
- SQL model `AuthSessionModel` (`shell/infrastructure/user/auth_session/persistence/sql/models/auth_session.py`);
- mappery SQL (`auth_session_entity_to_model`, `auth_session_model_to_entity`, `auth_session_update_model`);
- `SqlAuthSessionRepository` oraz symetryczny `InMemoryAuthSessionRepository`;
- rejestracja `AuthSessionRepository: SqlAuthSessionRepository` w `SqlAlchemyUserUnitOfWork._REPO_MAP`;
- migracja `072_create_auth_sessions.py`.

Port repozytorium:

- `save`;
- `get_by_id`;
- `get_by_token_hash` (rozpoznawanie sesji z cookie);
- `get_active_by_user_id(user_id, now)` — predykat "aktywna sesja" (nie revoked, nie deleted, niewygasla) mieszka w repozytorium, wzorzec jak `SessionRepository.get_open_by_user_id`; agregat nie ma publicznych metod `is_active`/`is_expired` — testy architektury wymagaja, by publiczne metody agregatu wywolywaly `append_event()`;
- `delete`, `exists`.

Do zrobienia:

- router i kontroler agregatu `AuthSession` w `shell/framework/user/auth_session/api/`;
- application handlers (`LoginAuthSessionCommand`/`LoginAuthSessionHandler`, `LogoutAuthSessionCommand`/`LogoutAuthSessionHandler`);
- middleware czytajacy cookie i ustawiajacy `request.state.current_user_id`.

Odczyt `User` moze sluzyc do walidacji, ale pojedynczy handler zapisuje tylko jeden agregat. Po poprawnym sprawdzeniu cookie odczytana wartosc `AuthSession.user_id` ustawia `request.state.current_user_id`.

Logowanie przez `/auth_session/login` wyszukuje `User` po emailu i sprawdza `User.status` bez modyfikowania agregatu `User`. Nastepnie handler `AuthSession` tworzy tylko `AuthSession` (get-or-create); po jego zapisaniu odpowiedz ustawia cookie i zwraca `AuthSession.id`.

Handler nie modyfikuje wiecej niz jednego agregatu w jednym commicie.

Usunac fallback `"system"` z operacji user-owned i ignorowac `user_id` przesylane przez klienta, gdy mozna wyznaczyc je z sesji.

### Migracja danych

1. Utworzona migracja `072_create_auth_sessions.py` — tabela `auth_sessions` z `user_id` jako foreign key do `user.id` (tabela w repo nazywa sie `user`, nie `users`).

   Kolumny: `id` (PK), `user_id` (FK -> `user.id`, NOT NULL), `token_hash` (VARCHAR 64, NOT NULL), `created_at` (NOT NULL), `expires_at` (NOT NULL), `revoked_at` (nullable), `updated_at` (nullable), `deleted_at` (nullable).

2. Nie migrowac starych login events do `auth_sessions`.
3. `users.email` pozostaje w bazie jako canonical email.
4. Unikalnosc loginu egzekwowac na `users.email` w formie normalized/case-insensitive.

## Frontend

### Platform auth

Istniejacy `libs/platform/auth-service` pozostaje jedynym publicznym serwisem logowania dla frontendu.

Zmiany:

- `login` wysyla tylko email do `/auth_session/login`;
- `initialize` wywoluje `/auth_session/me`;
- `logout` wywoluje `/auth_session/logout`;
- login nie korzysta z `/users/by-email`; getter pozostaje dostepny niezaleznie od logowania;
- nie przekazywac danych sesji do UI ani feature libraries.

`libs/platform/auth-store` pozostaje memory-only i przechowuje publiczny widok usera (`id`, `email`, `status`) oraz status. Frontend nie przechowuje identyfikatora sesji ani tokenow.

`libs/platform/api-client`:

- `withCredentials: true`;
- cookie-only flow z sesja przechowywana w `HttpOnly` cookie;
- po `401` wyczyscic auth store i przejsc do stanu unauthenticated;
- `apiFetch` i streaming korzystaja z tego samego cookie transportu.

### Usuniecie legacy

Po wdrozeniu backendowego kontraktu i migracji mockow usunac:

- `apps/shell-host/src/auth/auth-api.ts`;
- `libs/feature-user`;
- alias `@shell/feature-user`;
- root TypeScript project reference;
- allowliste testow architektury;
- wpisy lockfile przez zatwierdzony workflow.

Nie usuwac `libs/platform/event-bus`; jest aktywnie uzywany do notyfikacji auth/message.

## Cookies, CORS i CSRF

- session cookie: `HttpOnly`;
- `Secure` poza local HTTP;
- `SameSite=Lax` dla same-site albo `None` tylko z `Secure`;
- jawne origins, nigdy `*` razem z credentials;
- `Access-Control-Allow-Credentials: true`;
- podstawowa ochrona CSRF dla mutacji cookie-authenticated;
- cookie name, TTL i origins z konfiguracji.

## Mocki i testy

Frontend MSW musi implementowac stanowo:

- `/auth_session/login`;
- `/auth_session/me`;
- `/auth_session/logout`;
- expired/revoked session.

Chronione mocki nie moga przyjmowac dowolnego `user_id` z requestu jako zrodla tozsamosci.

Backend testy: agregat, use cases, migracja, endpointy, cookie, revokacja i user scoping.

Frontend testy: AuthService, API client concurrency/failure, bootstrap, LoginScreen z fake providerem, logout propagation i MSW.

E2E: login -> me -> dane domenowe scoped do usera -> logout -> `401`.

## Kolejnosc wdrozenia

1. Uzgodnic DTO, statusy i topology session cookie. **[ZROBIONE]** — kontrakt: `POST /auth_session/login` zwraca `{id}` sesji, `GET /auth_session/me` zwraca `{user_id}`, `POST /auth_session/logout` -> `204`; token tylko w `HttpOnly` cookie, nigdy w JSON.
2. Wdrozyc `AuthSession`, repozytorium, cookie i revocation. **[CZESCIOWO]** — domena, port, SQL/InMemory repo, model, migracja `072` zaimplementowane i zarejestrowane w UoW; brak middleware cookie i revocation endpointow.
3. Dodac application handler, router i middleware.
4. Usunac `system` fallback i dodac user scoping.
5. Przelaczyc frontendowy serwis logowania na obsluge cookie-only.
6. Rozszerzyc MSW i testy kontraktowe.
7. Usunac `feature-user` i `auth-api.ts` tylko jesli nie beda juz uzywane.
8. Pozostawic `/auth_session/login` oraz getter `/users/by-email`; getter nie uczestniczy w procesie logowania.
9. Zaktualizowac OpenAPI i dokumentacje.
10. Uruchomic Docker quality gates oraz E2E w obu repozytoriach.

## Kryteria akceptacji

- `User.email` jest jedynym source of truth dla loginu i danych kontaktowych.
- `User` przechowuje email i status biznesowy.
- `AuthSession` jest powiazana z `User` przez `user_id`.
- `AuthSession` jest niezalezna od workflow `Session`.
- Brak tokenow i danych auth w browser storage.
- Brak fallbacku `system` dla user-owned routes.
- Trzy endpointy `AuthSession` maja testy backend i frontend.
- `/auth_session/login` pozostaje endpointem logowania agregatu `AuthSession`.
- `/users/by-email` pozostaje getterem backendowym, ale nie uczestniczy w produkcyjnym flow logowania.
- Dokumentacja opisuje aktualny, a nie historyczny flow.

## Status wdrozenia — backend

### Zaimplementowane (2026-08-09)

- **Domain** `shell/domain/user/aggregates/auth_session/`:
  - agregat `AuthSession` (`create`, `restore`, `update`, `delete`, `revoke`);
  - `AuthSessionId` (VO);
  - eventy Created/Updated/Revoked/Deleted;
  - port `AuthSessionRepository` (`save`, `get_by_id`, `get_by_token_hash`, `get_active_by_user_id`, `delete`, `exists`);
  - `user_id` jako `UserId` z user BC (bez `UserIdRef` — ta sama granica BC).
- **Infrastructure** `shell/infrastructure/user/auth_session/persistence/`:
  - `AuthSessionModel` (`__tablename__ = "auth_sessions"`);
  - mappery SQL (round-trip: entity -> model -> entity);
  - `SqlAuthSessionRepository` + `InMemoryAuthSessionRepository` (symetryczne);
  - rejestracja w `SqlAlchemyUserUnitOfWork._REPO_MAP`.
- **Migracja** `072_create_auth_sessions.py` (tabela `auth_sessions`, FK -> `user.id`).

Decyzje projektowe:

- `GET /me` zwraca `{user_id}`; login zwraca tylko `{id}` sesji — spójnie z konwencja POST-ow w aplikacji.
- Predykat "aktywna sesja" w repozytorium (`get_active_by_user_id(user_id, now)`) — wzorzec `SessionRepository.get_open_by_user_id`; testy architektury nie pozwalaja na publiczne metody agregatu bez `append_event()`.
- Token: prosty symboliczny, w bazie tylko SHA-256 hash (`token_hash`), raw w `HttpOnly` cookie.

### Status prac

Wykonane:

- agregat `AuthSession`, eventy, repozytoria SQL/InMemory i migracja `072`;
- handlery login/logout/me, query service, router trzech endpointów i rejestracja DI;
- usunięty legacy `POST /users/login` wraz z `LoginUserCommand`, handlerem, eventami i automatycznym tworzeniem workflowowej `Session`;
- `GET /users/by-email` pozostawiony jako niezależny getter; `User.email` pozostaje źródłem prawdy.

Najbliższe prace:

- middleware cookie -> `request.state.current_user_id`;
- usunięcie fallbacku `"system"` z tras user-owned i user scoping;
- testy cookie, revocation, expiry, scoping, frontend cookie-only i E2E;
- aktualizacja frontendowych legacy referencji w osobnym checkoutcie, jeśli są nadal używane.

Workflowowa `Session` nie jest tworzona automatycznie przez `POST /auth_session/login`; pozostaje obsługiwana przez jawny endpoint/proces.
