---
name: saga
description: Wzorzec Saga w architekturze event-driven — koordynacja długotrwałych procesów biznesowych, kompensacja, choreografia vs orkiestracja, obsługa błędów i timeout. Używaj gdy operacja biznesowa rozciąga się na wiele agregatów/BC, wymaga kompensacji w razie błędu, albo potrzebuje koordynacji krok po kroku.
---

# Saga / Process Manager w Enterprise DDD

> **⚠️ UWAGA**: SHELL ma przewidzianą warstwę `shell/process/` dla sag, ale **NIE MA jeszcze żadnej implementacji**. Poniższe opisy są wzorcem docelowym.

## 1. Kiedy Używać Sagi

Saga jest potrzebna gdy **pojedyncza operacja biznesowa** rozciąga się na wiele agregatów/BC i wymaga:

- **Atomowości** — albo wszystkie kroki się udają, albo żaden (kompensacja)
- **Koordynacji** — krok B zależy od wyniku kroku A
- **Długiego trwania** — sekundy, minuty, dni (nie w jednej transakcji DB)
- **Komunikacji asynchronicznej** — przez eventy

Przykłady:
- Rezerwacja biletu lotniczego (hotel + lot + transfer)
- Przetwarzanie zamówienia (płatność + magazyn + wysyłka)
- Onboarding użytkownika (konto + uprawnienia + powiadomienie)

## 2. Choreografia vs Orkiestracja

| Kryterium | Choreografia | Orkiestracja |
|-----------|-------------|--------------|
| Liczba uczestników | 2-3 | 3+ |
| Złożoność logiki | Prosta | Złożona (warunki, pętle) |
| Widoczność przepływu | Rozproszona | Centralna |
| Trudność testowania | Średnia (wiele handlerów) | Niska (jeden orchestrator) |
| Modyfikacja przepływu | Wiele zmian | Jedno miejsce |
| Awaria orchestratora | N/D | Pojedynczy punkt awarii |

**Rekomendacja**: Zacznij od choreografii. Gdy logika robi się zbyt skomplikowana → migruj do orkiestracji.

## 3. Timeout i Retry w Sadze

Każdy krok sagi może mieć timeout — jeśli nie otrzymamy odpowiedzi w określonym czasie, uruchamiamy kompensację.

```python
class OrderSaga:
    async def start(self) -> None:
        self._state = SagaState.PAYMENT_PENDING
        await self._bus.publish(ProcessPaymentCommand(order_id=self._order_id))
        # Rezerwuj timeout — jeśli payment nie odpowie w 5 min, kompensuj
        await self._timeout_scheduler.schedule(
            saga_id=self._saga_id,
            timeout_after=Duration.minutes(5),
            on_timeout=self._on_payment_timeout,
        )

    async def _on_payment_timeout(self) -> None:
        if self._state == SagaState.PAYMENT_PENDING:
            self._state = SagaState.FAILED
            await self._bus.publish(OrderFailedEvent(
                order_id=self._order_id,
                reason="payment_timeout",
            ))
```

## 4. Lokalizacja w architekturze

Saga/Process Manager należy do warstwy **`process/`**, która leży między `application/` a `infrastructure/`:

```
domain/ ← application/ ← process/ ← infrastructure/ ← framework/
```

- `process/<bc>/<nazwa_sagi>/manager.py` — state machine
- `process/<bc>/<nazwa_sagi>/state.py` — stan sagi (trwały, w bazie)
- `process/<bc>/<nazwa_sagi>/handlers/` — event handlery delegujące do managera
- `process/<bc>/<nazwa_sagi>/commands/` — komendy produkowane tylko przez tę sagę
- `process/<bc>/<nazwa_sagi>/ports/` — porty (Protocol) dla repozytorium i command publishingu

> **Zasada**: Application = atomowe handlery (1 event → 1 agregat). Process = orchestracja (wiele agregatów, stan, koordynacja).

## 5. Podsumowanie — Checklista

Projektując Sagę:
- [ ] Choreografia dla prostych przypadków (2-3 uczestników)
- [ ] Orkiestracja dla złożonych przypadków (3+ uczestników)
- [ ] Saga w `process/`, nie w `application/`
- [ ] Idempotentność — wielokrotne wykonanie tego samego eventu
- [ ] Testy jednostkowe dla każdego przejścia stanu (`tests/process/unit/`)
- [ ] Testy integracyjne dla pełnego flow (`tests/process/integration/sql_sqlite/`)
