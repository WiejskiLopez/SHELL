# Anti-Corruption Layer — wzorzec krok po kroku

> Uwaga o konwencji ścieżek: poniższe przykłady (ordering, invoicing, legacy) są **ilustracyjne**. W SHELL nie ma top-level pakietów `shell/domain`, `shell/application` itd. — realna topologia to `shell/<service>/domain/<bc>/...` oraz `shell/<service>/application/<bc>/<aggregate>/...`. W każdym przykładzie zastąp `<service>` nazwą serwisu BC.

## Kiedy stosować ACL

ACL izoluje Twój BC od zewnętrznego systemu którego model danych jest "zepsuty", przestarzały albo który zmienia się bez ostrzeżenia.

**Użyj ACL gdy:**
- System zewnętrzny używa modelu danych niezgodnego z ubiquitous language Twojego BC
- System zewnetrzny udostepnia zmienny API i stosuje zmiany bez wersjonowania
- Integrujesz się z legacy systemem który nie może być zmodyfikowany
- System zewnętrzny używa formatów danych które nie pasują do Twojego modelu (XML, CSV, fixed-width)
- Migrujesz z legacy na nowy system (strangler fig)

**NIE używaj ACL gdy:**
- Oba BC są w ramach tego samego systemu (wystarczy port + adapter + QueryService)
- System zewnętrzny ma stabilne, dobrze udokumentowane API (wystarczy prosty adapter)

## Struktura ACL

```
┌──────────────────────────────────────────────────────────────────┐
│ Anti-Corruption Layer                                             │
│                                                                   │
│  ┌─────────────┐     ┌──────────────┐     ┌────────────────────┐ │
│  │ Translator  │────→│ Model Mapper  │────→│ External Gateway   │ │
│  │ (protocol)  │     │ (konwersja)   │     │ (HTTP / gRPC / SFTP)│ │
│  └─────────────┘     └──────────────┘     └────────────────────┘ │
│         │                                                         │
│         ▼                                                         │
│  BC Domain Model                                                  │
│  (InvoiceSummary, OrderStatus, CustomerInfo)                     │
└──────────────────────────────────────────────────────────────────┘
```

### Warstwy ACL

1. **External Gateway** — komunikacja techniczna z zewnętrznym systemem (HTTP client, gRPC stub, SSH klient). Odpowiedzialność: protokół transportowy, autoryzacja, retry.

2. **Model Mapper** — tłumaczenie zewnętrznego modelu na wewnętrzne VO/DTO. Tu żyje cała "brzydota": parsowanie XML, mapowanie dziwnych enumów, obsługa nulli, konwersje typów.

3. **Translator / Protocol** — interfejs który widzi domena/aplikacja. Czysty, stabilny, w ubiquitous language BC.

## Implementacja krok po kroku

### Krok 1: Zdefiniuj port w BC (Translator)

```python
# shell/domain/ordering/ports/legacy_customer_port.py
from __future__ import annotations
from typing import Protocol

from shell.domain.ordering.value_objects.customer_summary import CustomerSummary

class LegacyCustomerPort(Protocol):
    """Port do legacy CRM (system z lat 90)."""

    async def get_customer(self, customer_id: str) -> CustomerSummary | None:
        """Pobiera dane klienta z legacy CRM i zwraca w modelu Ordering BC."""
        ...

    async def get_customer_credit_limit(self, customer_id: str) -> Decimal:
        """Pobiera limit kredytowy klienta."""
        ...

    async def mark_customer_as_vip(self, customer_id: str) -> None:
        """Oznacza klienta jako VIP (zapis do legacy + nowy system)."""
        ...
```

### Krok 2: Zbuduj External Gateway

```python
# shell/infrastructure/ordering/adapters/legacy_crm_gateway.py
from __future__ import annotations
import httpx
import xml.etree.ElementTree as ET

class LegacyCrmGateway:
    """Gateway do legacy CRM — komunikacja przez XML over HTTP."""

    def __init__(self, base_url: str, username: str, password: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            auth=(username, password),
            timeout=30.0,
        )

    async def fetch_customer(self, customer_id: str) -> dict | None:
        response = await self._client.get(f"/api/v1/customers/{customer_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return self._parse_customer_xml(response.text)

    def _parse_customer_xml(self, xml: str) -> dict:
        root = ET.fromstring(xml)
        return {
            "customer_id": root.findtext("CUSTID"),
            "name": root.findtext("NAME"),
            "email": root.findtext("EMAIL"),
            "credit_amount": root.findtext("CREDITAMT"),
            "type_code": root.findtext("TYPECODE"),
            "is_active": root.findtext("ACTIVE") == "Y",
        }
```

### Krok 3: Zbuduj Model Mapper

```python
# shell/infrastructure/ordering/adapters/legacy_crm_mapper.py
from __future__ import annotations
from decimal import Decimal, InvalidOperation

from shell.domain.ordering.value_objects.customer_summary import CustomerSummary

class LegacyCrmMapper:
    """Mapowanie legacy CRM model → Ordering BC model."""

    def to_customer_summary(self, raw: dict) -> CustomerSummary:
        return CustomerSummary(
            id=raw["customer_id"],
            name=raw["name"].strip() if raw.get("name") else "Unknown",
            email=raw["email"],
            credit_limit=self._parse_decimal(raw.get("credit_amount")),
            customer_type=self._map_type_code(raw.get("type_code", "")),
            is_active=raw.get("is_active", False),
        )

    def _parse_decimal(self, value: str | None) -> Decimal:
        if not value:
            return Decimal("0")
        try:
            return Decimal(value)
        except InvalidOperation:
            return Decimal("0")

    def _map_type_code(self, code: str) -> str:
        # Legacy CRM: "R"=regular, "V"=VIP, "P"=partner, "I"=internal
        mapping = {"R": "regular", "V": "vip", "P": "partner", "I": "internal"}
        return mapping.get(code.upper(), "unknown")
```

### Krok 4: Zbuduj Adapter (spina wszystko)

```python
# shell/infrastructure/ordering/adapters/legacy_customer_adapter.py
from __future__ import annotations
from decimal import Decimal

from shell.domain.ordering.ports.legacy_customer_port import LegacyCustomerPort
from shell.infrastructure.ordering.adapters.legacy_crm_gateway import LegacyCrmGateway
from shell.infrastructure.ordering.adapters.legacy_crm_mapper import LegacyCrmMapper

class LegacyCustomerAdapter(LegacyCustomerPort):
    def __init__(self, gateway: LegacyCrmGateway, mapper: LegacyCrmMapper) -> None:
        self._gateway = gateway
        self._mapper = mapper

    async def get_customer(self, customer_id: str) -> CustomerSummary | None:
        raw = await self._gateway.fetch_customer(customer_id)
        if raw is None:
            return None
        return self._mapper.to_customer_summary(raw)

    async def get_customer_credit_limit(self, customer_id: str) -> Decimal:
        raw = await self._gateway.fetch_customer(customer_id)
        if raw is None:
            return Decimal("0")
        return self._mapper._parse_decimal(raw.get("credit_amount"))
```

## ACL a testy

Gateway jest izolowany — możesz testować mapper i adapter bez łączenia się z legacy systemem:

```python
async def test_customer_mapping():
    raw_data = {
        "customer_id": "C123",
        "name": "Acme Corp",
        "email": "acme@example.com",
        "credit_amount": "5000.00",
        "type_code": "V",
        "is_active": True,
    }
    mapper = LegacyCrmMapper()
    summary = mapper.to_customer_summary(raw_data)

    assert summary.id == "C123"
    assert summary.name == "Acme Corp"
    assert summary.credit_limit == Decimal("5000.00")
    assert summary.customer_type == "vip"


async def test_adapter_with_mock_gateway():
    class MockGateway:
        async def fetch_customer(self, customer_id: str):
            return {"customer_id": customer_id, "name": "Test", "email": "t@t.com",
                    "credit_amount": "100", "type_code": "R", "is_active": True}

    adapter = LegacyCustomerAdapter(
        gateway=MockGateway(),
        mapper=LegacyCrmMapper(),
    )
    customer = await adapter.get_customer("C1")
    assert customer is not None
    assert customer.credit_limit == Decimal("100")
```

## Wiele adapterów — jeden port

Gdy ten sam BC integruje się z wieloma systemami zewnętrznymi, każdy ma własny adapter implementujący ten sam port:

```python
# bootstrap/ordering/factory.py

if use_legacy_crm:
    customer_port = providers.Factory(LegacyCustomerAdapter, ...)
elif use_salesforce:
    customer_port = providers.Factory(SalesforceCustomerAdapter, ...)
else:
    customer_port = providers.Factory(ModernCrmCustomerAdapter, ...)

# Reszta BC nie zmienia się — wszyscy implementują ten sam LegacyCustomerPort
```

## Co NIE jest ACL

- **Prosty adapter** bez mapowania (woła zewnętrzne API i zwraca surowe dane) → to nie ACL, to gateway
- **Repository** ukrywające SQL → to nie ACL, to persistence adapter
- **DTO mapper** wewnątrz jednego BC → to nie ACL, to standardowy mapper
