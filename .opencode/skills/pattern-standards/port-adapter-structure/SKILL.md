---
name: port-adapter-structure
description: Reguły struktury Port i Adapter — port w domenie należy do potrzebującego, adapter w infrastrukturze, ACL dla systemów legacy, mapowanie typów.
---

# Port & Adapter Structure

> Reguły struktury Port i Adapter (Hexagonal Architecture) we wszystkich bounded contextach.

## Definicja

- Port to interfejs (Protocol/ABC) zdefiniowany w warstwie domenowej (lub aplikacyjnej). Definiuje **co** system robi; **jak** realizuje adapter.
- Adapter implementuje port w warstwie infrastruktury.

## Port

- Port jest własnością tego, kto GO POTRZEBUJE. Jeśli domena potrzebuje czasu → port `Clock` jest w domenie.

```python
class Clock(Protocol):
    def now(self) -> Timestamp: ...
    def today(self) -> Timestamp: ...
```

- Granulacja: jeden port na operację (złożona), jeden port na serwis (wiele powiązanych operacji), jeden port = jedna metoda (prosta, izolowana).
- Port jest stabilny — ewolucja przez dodawanie metod; istniejące sygnatury pozostają bez zmian.

```python
# Stabilność: nowe metody dodawane, istniejące sygnatury bez zmian
class NotificationPort(Protocol):
    async def send_email(self, to: EmailAddress, subject: str, body: str) -> None: ...
    async def send_sms(self, to: PhoneNumber, message: str) -> None: ...  # nowa metoda
```

## Adapter

- Implementuje port w infrastrukturze.
- Jedyny komponent który zna zewnętrzny system.
- Adapter mapuje typy źródłowe na typy docelowe; surowe DTO źródła pozostają po stronie źródła.
- Adapter wykonuje tłumaczenie typów; logika biznesowa pozostaje w domenie.
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

## Kontrakt graniczny (koperta/transport) żyje obok portu

- Kontrakt wire (koperta delivery, np. `EventDeliveryEnvelope`/`CommandDeliveryEnvelope`, oraz
  typy argumentów/zwrotów portu transportu) definiuje się **w warstwie wewnętrznej przy porcie**,
  w `application/ports/transport/`, a **nie w infrastrukturze**.
- Powód (reguła zależności): port `DeliveryTransport` jest kontraktem aplikacyjnym, więc jego
  typy wejścia/wyjścia (koperta) muszą być widoczne z `application/`. Umieszczenie koperty
  w `infrastructure/messaging/delivery/` wymuszałoby import infrastruktury z warstwy aplikacji
  (odwrócenie zależności) albo duplikację kontraktu.
- Adapter (np. `RabbitEventDeliveryTransport`) implementuje port i importuje kopertę z
  `application/ports/` — koperta nie jest szczegółem technicznym, lecz jawnym kontraktem granicy.
- Koperta transportowa może być „czysto techniczna" (w infrastrukturze) **wyłącznie wtedy**, gdy
  nie jest kontraktem konsumowanym przez porty aplikacji (np. wewnętrzny detal brokera).

## Lokalizacja

- Porty platformy: `shell/platform/domain/ports/` (Clock, IdGenerator, RepositoryPort)
- Adaptery platformy: `shell/platform/infrastructure/time/`, `shell/platform/infrastructure/identity/`
- Adaptery BC: `shell/<service>/infrastructure/<bc>/<aggregate>/adapters/<port_name>/` (wzorce Provider / Command Port) oraz `shell/<service>/infrastructure/<bc>/acl/`

Lokalizację portów wyjściowych konkretnego agregatu (katalogi `repositories/`,
`ports/`) i ich adapterów opisują dedykowane wzorce: Repository, Aggregate Provider i Command Port.
