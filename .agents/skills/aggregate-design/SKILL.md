---
name: aggregate-design
description: Zasady projektowania agregatów DDD — wyznaczanie granic, enkapsulacja stanu, referencje przez ID, optymistyczne blokowanie, maszyny stanów. Używaj gdy modelujesz nowy agregat, refaktoryzujesz istniejący, dzielisz za duży agregat, albo nie jesteś pewien gdzie postawić granicę transakcyjną.
---

# Projektowanie agregatów DDD

Agregat to podstawowa jednostka konsystencji transakcyjnej w DDD. Każdy agregat ma jeden Aggregate Root — encję przez którą odbywa się cały dostęp do agregatu z zewnątrz.

## Cztery zasady Vaughna Vernona

Każdy projekt agregatu weryfikuj przez te cztery pytania:

### 1. Czy agregat jest wystarczająco mały?

Agregat zawiera dokładnie tyle encji/VO, ile potrzeba do zachowania invariantów biznesowych w jednej transakcji. Nie ładuj całego grafu obiektów do jednego agregatu "bo będzie wygodniej".

Sygnały że agregat jest za duży:
- Pojedynczy zapis dotyka wielu kolekcji wewnątrz agregatu
- Różne przypadki użycia modyfikują kompletnie różne części tego samego agregatu
- Dwie encje wewnątrz agregatu są zawsze modyfikowane w różnych transakcjach
- Zapis agregatu trwa długo (dużo danych), bo ładujesz rzeczy niepotrzebne do bieżącej operacji

### 2. Czy zachowuję invariants natychmiastowo?

Invariant to reguła biznesowa która MUSI być spełniona zawsze, bez żadnego okna czasowego. Jeśli dwie encje muszą być spójne natychmiast (w tej samej transakcji) — są w tym samym agregacie. Jeśli mogą być spójne ostatecznie (eventual consistency) — są w różnych agregatach.

```python
# Ten invariant wymaga natychmiastowej spójności: suma itemów nie może przekroczyć limitu
# Więc Order i OrderItem są w tym samym agregacie
class Order(AggregateRoot[OrderId]):
    def add_item(self, item: OrderItem) -> None:
        if self._total_value + item.value > self._limit:
            raise OrderLimitExceeded(self.id)
        self._items.append(item)
        self._total_value += item.value

# Ten invariant może być spełniony w osobnej transakcji:
# "Po opłaceniu zamówienia zarezerwuj produkty w magazynie"
# → różne agregaty, komunikacja przez eventy
```

### 3. Czy referencje między agregatami są przez ID?

Agregat A nigdy nie trzyma referencji do obiektu agregatu B. Trzyma tylko `B_id`. Relacje między agregatami nawigujesz przez repository, nie przez object graph.

```python
# POPRAWNIE — referencja przez ID
class Order(AggregateRoot[OrderId]):
    __slots__ = ("_customer_id", ...)  # CustomerId, nie Customer

# ŹLE — referencja obiektowa
class Order(AggregateRoot[OrderId]):
    __slots__ = ("_customer", ...)     # Customer — obcy agregat
```

### 4. Czy rozmiar transakcji jest minimalny?

Pojedyncza transakcja modyfikuje DOKŁADNIE JEDEN agregat. Jeśli musisz zapisać dwa agregaty w jednej operacji — użyj eventual consistency: pierwszy agregat zapisuje się i emituje event, drugi subskrybuje ten event i zapisuje się w osobnej transakcji.

Wyjątek: dwa agregaty w jednej transakcji są akceptowalne tylko gdy oba są nowe (tworzone) i żaden inny proces nie może ich współbieżnie modyfikować. Ale to sygnał że może powinny być jednym agregatem.

```python
# POPRAWNIE — jeden agregat na transakcję
async with unit_of_work as unit_of_work:
    order = await unit_of_work.orders.get_by_id(order_id)
    order.confirm()
    unit_of_work.stage_events(order.pull_events())
# OrderConfirmedEvent → InventoryHandler (osobna transakcja) → rezerwuje stock

# ŹLE — dwa agregaty w jednej transakcji (chyba że oba są nowe)
async with unit_of_work as unit_of_work:
    order = await unit_of_work.orders.get_by_id(order_id)
    inventory = await unit_of_work.inventories.get_by_id(product_id)
    order.confirm()
    inventory.reserve(product_id, order.quantity)  # deadlock, concurrency hell
    unit_of_work.stage_events(order.pull_events())
    unit_of_work.stage_events(inventory.pull_events())
```

## Enkapsulacja stanu

Stan agregatu jest modyfikowalny WYŁĄCZNIE przez metody domenowe. Żadnych publicznych setterów. Żadnych mutowalnych referencji z property.

```python
class Workflow(AggregateRoot[WorkflowId]):
    __slots__ = ("_status", "_cursor", ...)

    # POPRAWNIE — tylko getter
    @property
    def status(self) -> Status:
        return self._status

    # POPRAWNIE — metoda biznesowa
    def start_at(self, now: datetime) -> None:
        self._status = Status.running()
        self._started_at = now
        self.append_event(WorkflowStartedEvent.now(self.id, now=now))

    # ŹLE — publiczny setter
    # @status.setter
    # def status(self, value): ...
```

Property zwracające kolekcje zwracają kopie (płytkie lub głębokie):

```python
@property
def items(self) -> tuple[OrderItem, ...]:
    return tuple(self._items)

@property
def metadata(self) -> dict[str, str]:
    return dict(self._metadata)
```

## Maszyna stanów na agregacie

Przejścia stanu są jawne, nazwane językiem domeny i emitują eventy bezwarunkowo:

```python
class Workflow(AggregateRoot[WorkflowId]):
    def start_at(self, now: datetime) -> None:
        if self._status != Status.idle():
            raise InvalidStateTransition(self.id, self._status, Status.running())
        self._status = Status.running()
        self.append_event(WorkflowStartedEvent.now(self.id, now=now))

    def finish(self, now: datetime) -> None:
        if self._status != Status.running():
            raise InvalidStateTransition(self.id, self._status, Status.done())
        self._status = Status.done()
        self.append_event(WorkflowCompletedEvent.now(self.id, now=now))

    def abort(self, reason: str, now: datetime) -> None:
        self._status = Status.failed()
        self.append_event(WorkflowFailedEvent.now(self.id, reason=reason, now=now))
```

Zasady:
- Każda metoda domenowa woła `append_event()` z odpowiednim DomainEvent
- Event przejścia stanu emitowany **bezwarunkowo** — nie zależy od opcjonalnych parametrów metody
- Sprawdzaj warunek wejściowy (guard clause) na początku metody

## Optymistyczne blokowanie (optimistic concurrency)

Każdy agregat trzyma `_version` inkrementowany przy każdym zapisie. Repository CAS (compare-and-swap) przy zapisie sprawdza czy wersja w bazie jest zgodna z tą z pamięci.

```python
class AggregateRoot(Generic[TId]):
    __slots__ = ("_id", "_version")

    def __init__(self, id: TId, version: int = 1) -> None:
        self._id = id
        self._version = version

    @property
    def version(self) -> int:
        return self._version

# W repozytorium:
async def save(self, aggregate: AggregateRoot) -> None:
    result = await self._session.execute(
        update(AggregateModel)
        .where(AggregateModel.id == aggregate.id.value)
        .where(AggregateModel.version == aggregate.version)  # CAS
        .values(version=aggregate.version + 1, ...)
    )
    if result.rowcount == 0:
        raise ConcurrentModification(aggregate.id, aggregate.version)
```

## Kiedy czytasz references

- Wyznaczasz granice nowego agregatu → `references/aggregate-heuristics.md`
- Debugujesz problem z konsystencją, wydajnością albo blokadami → `references/aggregate-anti-patterns.md`

## Konwencje

- Agregat dziedziczy po `AggregateRoot[TId]`
- `__slots__` bez powtarzania `_id` (dziedziczony)
- Każda metoda biznesowa woła `append_event()`
- Eventy pullowane przez handler przez `aggregate.pull_events()` + `unit_of_work.stage_events()`
- Nigdy `@dataclass` dla agregatu — identity-based equality

## Struktura folderów agregatu

W folderze agregatu znajduje się **wyłącznie** plik agregatu (klasa dziedzicząca po `AggregateRoot`).
Wszystkie value objects (w tym ID) należą do podfolderu `value_objects/` wewnątrz agregatu:

```
aggregates/my_aggregate/
    __init__.py
    my_aggregate.py                          # tylko agregat
    value_objects/
        __init__.py
        my_aggregate_id.py                   # ID jako VO
        my_aggregate_skill_id.py             # inne VO
        child_entity_id.py
```

Importy wewnątrz agregatu zawsze wskazują na `value_objects`:

```python
# my_aggregate.py
from .value_objects.my_aggregate_id import MyAggregateId
from .value_objects.my_aggregate_skill_id import MyAggregateSkillId
```

Wszystkie value objects są wprost w `value_objects/` — bez dodatkowych podfolderów.
