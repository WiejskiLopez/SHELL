---
name: port-adapter-structure
description: Reguły struktury Port i Adapter — port w domenie należy do potrzebującego, adapter w infrastrukturze, ACL dla systemów legacy, mapowanie typów.
---

# Port & Adapter Structure

> Reguły struktury Port i Adapter (Hexagonal Architecture) we wszystkich bounded contextach.

## Definicja

- Port to interfejs (Protocol/ABC) zdefiniowany w warstwie domenowej (lub aplikacyjnej). Definiuje **co** system robi, nie **jak**.
- Adapter implementuje port w warstwie infrastruktury.

## Port

- Port jest własnością tego, kto GO POTRZEBUJE. Jeśli domena potrzebuje czasu → port `Clock` jest w domenie.

```python
class Clock(Protocol):
    def now(self) -> Timestamp: ...
    def today(self) -> Timestamp: ...
```

- Granulacja: jeden port na operację (złożona), jeden port na serwis (wiele powiązanych operacji), jeden port = jedna metoda (prosta, izolowana).
- Port jest stabilny — zmiany przez dodawanie, nie modyfikacje.

```python
# Stabilność: dodajemy nową metodę, nie zmieniamy istniejących
class NotificationPort(Protocol):
    async def send_email(self, to: EmailAddress, subject: str, body: str) -> None: ...
    async def send_sms(self, to: PhoneNumber, message: str) -> None: ...  # nowa metoda
```

## Adapter

- Implementuje port w infrastrukturze.
- Jedyny komponent który zna zewnętrzny system.
- Adapter mapuje: typy źródłowe → typy docelowe (nigdy nie przepuszcza surowych DTO źródła).
- Adapter nie zawiera logiki biznesowej — tylko tłumaczenie.
- Wyjątki z adaptera mapowane na domenowe.

```python
class EmailNotificationAdapter:
    def __init__(self, smtp_client: SmtpClient) -> None:
        self._smtp_client = smtp_client

    async def send_email(self, to: EmailAddress, subject: str, body: str) -> None:
        try:
            await self._smtp_client.send(
                to=to.value,
                subject=subject,
                body=body,
            )
        except SmtpConnectionError as e:
            raise NotificationDeliveryError(to, str(e)) from e
```

## Anti-Corruption Layer

- Gdy BC komunikuje się z systemem legacy / zewnętrznym, ACL izoluje BC od 'zepsutego' modelu danych zewnętrznego systemu.
- Stosuj gdy: integracja z systemem legacy, zewnętrzne API o słabym/zmiennym kontrakcie, migracja (strangler fig pattern), third-party SaaS.

## Porty serwisów domenowych i adaptery (wzorzec `services/`)

Gdy agregat A potrzebuje danych z zewnątrz (inny agregat tego samego BC, subdomena, zewnętrzny mikroserwis, usługa techniczna jak generator tokena), konsumujący definiuje **port w swoim podfolderze**, a implementacja ląduje w **infrastrukturze tego samego agregatu**.

### Lokalizacja

```
# Port (domena konsumująca)
shell/domain/<bc>/aggregates/<agregat>/services/
    <nazwa_portu>.py                      # np. token_generator.py, workflow_data_port.py

# Adapter (infrastruktura tego samego agregatu)
shell/infrastructure/<bc>/<aggregate>/services/
    <nazwa_adaptera>.py                   # np. secure_token_generator.py, sql_workflow_data_adapter.py
```

Port i adapter leżą w poddrzewie **tego samego agregatu**, który ich potrzebuje — nie w wydzielonym katalogu `services/` na poziomie BC, nie obok persystencji (`persistence/`). Folder `services/` agregatu w infrastrukturze skupia wyłącznie zewnętrzne implementacje portów tego agregatu.

Przykład (agregat `AuthSession`, BC `user`):

```
shell/domain/user/aggregates/auth_session/services/
    token_generator.py                     # class TokenGenerator(Protocol): generate() -> str

shell/infrastructure/user/auth_session/services/
    secure_token_generator.py              # class SecureTokenGenerator: generate() -> str
```

### Zasady

1. **Adapter implementuje port konsumującego** — port w `shell/domain/<bc>/aggregates/<agregat>/services/`, adapter w `shell/infrastructure/<bc>/<aggregate>/services/`.
2. **Mapowanie na VO konsumującego** — adapter pobiera dane ze źródła (repozytorium, HTTP API, gRPC) i mapuje na Value Objecty domeny konsumującej. Nigdy nie przepuszcza surowych DTO źródła.
3. **Async** — metody adaptera pobierające dane są `async` (usługi techniczne, np. generator tokena, mogą być synchroniczne).
4. **Error handling** — błędy sieciowe/timeouty są łapane i opakowywane w dedykowane wyjątki domenowe (np. `WorkflowDataUnavailable`). Adapter nie propaguje surowych wyjątków HTTP/transportowych.
5. **Retry / Circuit Breaker** — stosowany na poziomie adaptera, nie domeny.
6. **Domain service korzysta z portu, nie z adaptera** — serwis domenowy (`AuthSessionManagementService`) dostaje port wstrzyknięty w konstruktorze; decyzje podejmuje na danych z portu, nigdy nie woła infrastruktury.

```python
# Port (domain/<bc>/aggregates/<agregat>/services/user_lookup_port.py)
class UserLookupPort(Protocol):
    async def get_by_email(self, email: UserEmail) -> User | None: ...
```

```python
# Adapter (infrastructure/<bc>/<aggregate>/services/sql_user_lookup_adapter.py)
class SqlUserLookupAdapter:
    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def get_by_email(self, email: UserEmail) -> User | None:
        return await self._repo.get_by_email(email)
```

```python
# Adapter HTTP (po ekstrakcji mikroserwisu — reszta systemu bez zmian)
class HttpUserLookupAdapter:
    def __init__(self, http_client: HttpClient) -> None:
        self._http_client = http_client

    async def get_by_email(self, email: UserEmail) -> User | None:
        try:
            raw = await self._http_client.get(f"/users/by-email?email={email.value}")
            return User.restore(...)
        except HttpTimeoutError as e:
            raise UserLookupUnavailable(email) from e
```

### Minimalizacja coupling

Dzięki tej strukturze wydzielenie agregatu do osobnego mikroserwisu wymaga tylko:
1. Skopiowania folderu `infrastructure/<bc>/<aggregate>/services/` do nowego serwisu.
2. Zmiany implementacji adapterów (lokalne repo → HTTP).
3. Reszta systemu (domena, aplikacja, handlery) — **zero zmian**.

> **Porty tych adapterów → [domain-service-structure](../domain-service-structure/SKILL.md#porty-do-pobierania-danych-międzyagregatowych)**

## Lokalizacja

- Porty: `shell/domain/platform/ports/` (uniwersalne), `shell/domain/<bc>/aggregates/<agregat>/repositories/` (repozytoria), `shell/domain/<bc>/aggregates/<agregat>/services/` (serwisy i porty serwisów domenowych)
- Adaptery: `shell/infrastructure/platform/time/`, `shell/infrastructure/platform/identity/`, `shell/infrastructure/<bc>/<aggregate>/persistence/sql/repositories/`, `shell/infrastructure/<bc>/<aggregate>/persistence/memory/`, `shell/infrastructure/<bc>/<aggregate>/services/`, `shell/infrastructure/<bc>/http/`, `shell/infrastructure/<bc>/acl/`
