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

## Lokalizacja

- Porty: `shell/domain/platform/ports/` (uniwersalne), `shell/domain/<bc>/repositories/` (repozytoria), `shell/domain/<bc>/services/ports.py` (serwisy)
- Adaptery: `shell/infrastructure/platform/adapters/`, `shell/infrastructure/<bc>/repositories/`, `shell/infrastructure/<bc>/adapters/`, `shell/infrastructure/<bc>/acl/`
