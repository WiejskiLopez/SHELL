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

## Adaptery cross-aggregate data retrieval

Adaptery do pobierania danych z innych agregatów (w obrębie BC, subdomeny lub zewnętrznego mikroserwisu) implementują port zdefiniowany w domenie konsumującej.

### Lokalizacja

```
shell/infrastructure/<bc>/services/
    <nazwa_agregatu>/
        workflow_data_adapter.py
        eligibility_adapter.py
```

Folder `<nazwa_agregatu>` skupia wszystkie adaptery związane z danym agregatem. Jeśli agregat zostanie wydzielony do osobnego mikroserwisu, cały folder jest przenoszony — adaptery zaczynają wołać HTTP zamiast lokalnego repozytorium, a reszta systemu (domena, aplikacja) pozostaje bez zmian.

### Zasady

1. **Adapter implementuje port konsumującego** — port jest w `shell/domain/<konsumujący_bc>/services/`, adapter w `shell/infrastructure/<konsumujący_bc>/services/<nazwa_agregatu>/`.
2. **Mapowanie na VO konsumującego** — adapter pobiera dane ze źródła (repozytorium, HTTP API, gRPC) i mapuje na Value Objecty domeny konsumującej. Nigdy nie przepuszcza surowych DTO źródła.
3. **Async** — każda metoda adaptera jest `async`.
4. **Error handling** — błędy sieciowe/timeouty są łapane i opakowywane w dedykowane wyjątki domenowe (np. `WorkflowDataUnavailable`). Adapter nie propaguje surowych wyjątków HTTP/transportowych.
5. **Retry / Circuit Breaker** — stosowany na poziomie adaptera, nie domeny.

```python
# Adapter lokalny (przed ekstrakcją mikroserwisu)
class LocalEligibilityAdapter:
    def __init__(self, repo: EligibilityRepository, mapper: EligibilityMapper) -> None:
        self._repo = repo
        self._mapper = mapper

    async def check(self, customer_id: CustomerId) -> Eligibility:
        model = await self._repo.get_by_customer_id(customer_id)
        return self._mapper.to_domain(model)
```

```python
# Adapter HTTP (po ekstrakcji mikroserwisu — reszta systemu bez zmian)
class HttpEligibilityAdapter:
    def __init__(self, http_client: HttpClient) -> None:
        self._http_client = http_client

    async def check(self, customer_id: CustomerId) -> Eligibility:
        try:
            raw = await self._http_client.get(
                f"/eligibility/{customer_id.value}"
            )
            return Eligibility.from_dict(raw)
        except HttpTimeoutError as e:
            raise EligibilityDataUnavailable(customer_id) from e
```

### Minimalizacja coupling

Dzięki tej strukturze wydzielenie agregatu do osobnego mikroserwisu wymaga tylko:
1. Skopiowania folderu `infrastructure/<bc>/services/<agregat>/` do nowego serwisu.
2. Zmiany implementacji adapterów (lokalne repo → HTTP).
3. Reszta systemu (domena, aplikacja, handlery) — **zero zmian**.

> **Porty tych adapterów → [domain-service-structure](../domain-service-structure/SKILL.md#porty-do-pobierania-danych-międzyagregatowych)**

## Lokalizacja

- Porty: `shell/domain/platform/ports/` (uniwersalne), `shell/domain/<bc>/aggregates/<agregat>/repositories/` (repozytoria), `shell/domain/<bc>/aggregates/<agregat>/services/` (serwisy)
- Adaptery: `shell/infrastructure/platform/time/`, `shell/infrastructure/platform/identity/`, `shell/infrastructure/<bc>/<aggregate>/persistence/sql/repositories/`, `shell/infrastructure/<bc>/<aggregate>/persistence/memory/`, `shell/infrastructure/<bc>/http/`, `shell/infrastructure/<bc>/acl/`
