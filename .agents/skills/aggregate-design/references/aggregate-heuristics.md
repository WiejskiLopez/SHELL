# Heurystyki wyznaczania granic agregatu

## Heurystyka 1: Invariant biznesowy

Zadaj pytanie: *"Które dane muszą być spójne w tej samej milisekundzie, a które mogą być spójne za sekundę?"*

To co musi być spójne natychmiast → ten sam agregat.
To co może być spójne ostatecznie → różne agregaty, komunikacja przez eventy.

```
Przykład: System rezerwacji

Agregat Reservation:
- invariant: "suma zarezerwowanych miejsc ≤ pojemność sali"
- weryfikowane przy każdej rezerwacji w jednej transakcji
→ Reservation to agregat z kolekcją ReservationItem

Agregat Invoice:
- tworzony po potwierdzeniu rezerwacji
- nie musi być spójny natychmiast z Reservation
→ osobny agregat, tworzony po ReservationConfirmedEvent
```

## Heurystyka 2: Granica właściciela (root entity)

Zadaj pytanie: *"Która encja jest właścicielem pozostałych? Która encja 'rządzi' pozostałymi?"*

Właściciel (root) jest Aggregate Root. Encje które nie mogą istnieć bez roota są wewnątrz tego samego agregatu.

```
Order → OrderItem     (item nie istnieje bez zamówienia)
Workflow → Cursor     (kursor nie istnieje bez workflow)
Graph → Node          (node nie istnieje bez grafu)
```

Encje które mogą istnieć niezależnie → osobne agregaty.

```
Customer ≠ Order      (klient istnieje bez zamówienia)
Product ≠ OrderItem   (produkt istnieje niezależnie)
User ≠ Session        (użytkownik istnieje niezależnie od sesji)
```

## Heurystyka 3: Granica transakcji (use case boundary)

Zadaj pytanie: *"Ile przypadków użycia modyfikuje tę samą encję?"*

Jeśli encja jest modyfikowana przez wiele, niepowiązanych przypadków użycia — prawdopodobnie jest za duża i zawiera wiele agregatów w jednym.

Jeśli encja jest modyfikowana przez dokładnie jeden przypadek użycia (albo kilka bardzo powiązanych) — granica jest prawidłowa.

```
Sygnał ostrzegawczy:
- 15 handlerów modyfikuje ten sam agregat w zupełnie różnych celach
- Każdy handler modyfikuje tylko 2-3 pola z 20 dostępnych
- Współbieżne zapisy do tego samego agregatu z różnych handlerów stale powodują concurrency conflicts
```

## Heurystyka 4: Granica czasu życia

Zadaj pytanie: *"Czy te encje są tworzone i usuwane razem?"*

Encje które dzielą ten sam cykl życia → ten sam agregat.
Encje które mają różne cykle życia → różne agregaty.

```
Workflow + WorkflowCursor — tworzone razem, kończą się razem → ten sam agregat
Workflow + TaskExecution — różne cykle życia, TaskExecution może przeżyć wiele workflow → różne agregaty
```

## Heurystyka 5: Zasada małych agregatów

Zaczynaj od małych agregatów. Łatwiej połączyć dwa małe agregaty niż rozbić jeden za duży.

Domyślna reguła: agregat = pojedyncza encja root + jej silnie zależne child entity + value objects. Jeśli nie masz pewności czy dwie encje powinny być w tym samym agregacie — trzymaj je osobno i łącz przez eventy.

```python
# Minimalny agregat — sam root, zero child entities
class Customer(AggregateRoot[CustomerId]):
    __slots__ = ("_name", "_email", "_status")
    # ... metody domenowe

# Mały agregat — root + child entity
class Order(AggregateRoot[OrderId]):
    __slots__ = ("_customer_id", "_items", "_status")
    # OrderItem to child entity bez własnej tożsamości globalnej
```

## Decyzje "rozbić czy nie"

| Sygnał | Decyzja |
|--------|---------|
| Dwa różne use case'y zawsze modyfikują różne części tego samego agregatu | Rozbij na dwa |
| Dwie encje nigdy nie są ładowane razem (zawsze tylko jedna z nich) | Rozbij |
| Concurrency conflicts stale dotyczą różnych pól tego samego agregatu | Rozbij |
| Metoda biznesowa potrzebuje invariantu na danych z obu encji natychmiast | Trzymaj razem |
| Encje mają różne cykle życia (jedna przeżywa drugą) | Rozbij |
| Dwa różne zespoły modyfikują różne części agregatu | Rozbij (to też sygnał organizacyjny) |

## Eventual consistency — praktyczna implementacja

Gdy rozbijasz agregat A na A i B:

1. A zapisuje się w transakcji T1, emituje event E_A
2. Event handler subskrybujący E_A ładuje B, modyfikuje, zapisuje w transakcji T2
3. Jeśli T2 fail — event E_A wraca do kolejki (outbox relay retry)
4. Handler B musi być idempotentny (patrz skill `event-driven-integration`)

```
Przykład: Order → Inventory (osobne agregaty)

T1: Order.confirm()
    → OrderConfirmedEvent { order_id, product_id, quantity }

T2: InventoryHandler.handle(OrderConfirmedEvent)
    → inventory = repo.get_by_product_id(event.product_id)
    → inventory.reserve(event.order_id, event.quantity)
    → save + stage_events

Jeśli T2 nie może zarezerwować (brak stanu):
    → Inventory.reserve() rzuca InsufficientStock
    → handler emituje ReservationFailedEvent
    → OrderCancelHandler cofa zamówienie (compensating action)
```
