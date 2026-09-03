# Antywzorce projektowania agregatów

## 1. Anemiczny model domenowy (Anemic Domain Model)

**Na czym polega.** Agregat to tylko struktura danych z getterami i setterami. Cała logika biznesowa jest w serwisach/handlerach.

```python
# ŹLE — anemiczny model
class Order(AggregateRoot[OrderId]):
    @property
    def status(self) -> Status: return self._status
    @status.setter
    def status(self, value): self._status = value

    @property
    def items(self) -> list[OrderItem]: return self._items
    @items.setter
    def items(self, value): self._items = value

# Handler robi wszystko:
async def handle(self, confirm_order_command: ConfirmOrderCommand) -> None:
    async with self._unit_of_work as unit_of_work:
        order = await unit_of_work.orders.get_by_id(confirm_order_command.order_id)
        if order.status != Status.pending():
            raise InvalidState()
        order.status = Status.confirmed()        # setter z zewnątrz!
        order.confirmed_at = datetime.now()      # setter!
        await unit_of_work.orders.save(order)
```

**Dlaczego to boli.** Logika biznesowa rozproszona po handlerach — każdy handler implementuje własną wersję tych samych reguł. Invarianty nie są egzekwowane w jednym miejscu. Nie da się stwierdzić czy stan agregatu jest prawidłowy patrząc tylko na niego.

**Prawidłowy wzorzec.** Logika biznesowa w metodach domenowych agregatu:

```python
# POPRAWNIE — rich domain model
class Order(AggregateRoot[OrderId]):
    def confirm(self, now: datetime) -> None:
        if self._status != Status.pending():
            raise InvalidStateTransition(self.id, self._status, Status.confirmed())
        self._status = Status.confirmed()
        self._confirmed_at = now
        self.append_event(OrderConfirmedEvent.now(self.id, now=now))

# Handler tylko orkiestruje:
async def handle(self, confirm_order_command: ConfirmOrderCommand) -> None:
    async with self._unit_of_work as unit_of_work:
        order = await unit_of_work.orders.get_by_id(confirm_order_command.order_id)
        order.confirm(now=datetime.now())
        unit_of_work.stage_events(order.pull_events())
```

## 2. Za duży agregat (Big Ball of Mud Aggregate)

**Na czym polega.** Jeden agregat zawiera zbyt wiele encji. Pojedynczy `save()` ładuje i zapisuje pół bazy danych "bo wszystko jest ze sobą powiązane".

```python
# ŹLE — jeden wielki agregat
class Company(AggregateRoot[CompanyId]):
    __slots__ = (
        "_name", "_address", "_departments",  # 50 departamentów
        "_employees",                          # 5000 pracowników
        "_projects",                           # 200 projektów
        "_invoices",                           # 10 000 faktur
        "_settings", "_audit_log", ...
    )
```

**Dlaczego to boli.**
- Wydajność: każdy odczyt/zapis ładuje ogromny graf obiektów
- Concurrency: wiele handlerów walczy o ten sam agregat → stale concurrency conflicts
- Testowalność: nie da się testować pojedynczych funkcji bez ładowania całego agregatu
- Czytelność: 2000 linii w jednej klasie

**Prawidłowy wzorzec.** Rozbij na małe agregaty:

```python
class Company(AggregateRoot[CompanyId]):
    __slots__ = ("_name", "_address", "_settings")

class Department(AggregateRoot[DepartmentId]):
    __slots__ = ("_company_id", "_name")        # referencja przez ID

class Employee(AggregateRoot[EmployeeId]):
    __slots__ = ("_department_id", "_name", ...)

class Project(AggregateRoot[ProjectId]):
    __slots__ = ("_company_id", "_name", ...)
```

## 3. Referencje obiektowe między agregatami

**Na czym polega.** Agregat A trzyma instancję agregatu B zamiast jego ID.

```python
# ŹLE
class Order(AggregateRoot[OrderId]):
    __slots__ = ("_customer", ...)  # obiekt Customer, nie CustomerId

# Handler:
order = await unit_of_work.orders.get_by_id(order_id)
customer_name = order.customer.name  # lazy load, N+1, transakcja rozszerzona
```

**Dlaczego to boli.**
- Lazy loading (SELECT N+1)
- Rozszerzona transakcja (dwa agregaty w jednej sesji)
- Niezdefiniowana granica transakcyjna
- Przy serializacji (cache, event) ciągniesz cały graf

**Prawidłowy wzorzec.** Tylko ID + jawny lookup przez repository gdy potrzebne:

```python
class Order(AggregateRoot[OrderId]):
    __slots__ = ("_customer_id", ...)  # tylko ID

# Handler gdy potrzebuje danych klienta:
customer = await unit_of_work.customers.get_by_id(order.customer_id)
```

## 4. Brak enkapsulacji — publiczne settery dla stanu domenowego

**Na czym polega.** Stan agregatu jest modyfikowany z zewnątrz przez settery zamiast metod domenowych.

```python
# ŹLE — każdy może zmienić stan
workflow.status = Status.done()
workflow.cursor = new_cursor
```

**Dlaczego to boli.** Invarianty nie są sprawdzane. Eventy nie są emitowane. Stan może być nieprawidłowy.

**Prawidłowy wzorzec.** Wszystkie mutacje przez metody domenowe:

```python
workflow.advance_to(node_index=3, now=datetime.now())
```

## 5. Logika biznesowa w serwisach aplikacyjnych

**Na czym polega.** Reguły biznesowe są zaimplementowane w handlerze/serwisie zamiast w agregacie.

```python
# ŹLE — handler sprawdza reguły
async def handle(self, command):
    async with self._unit_of_work as unit_of_work:
        order = await unit_of_work.orders.get_by_id(command.order_id)
        # Reguła biznesowa w handlerze:
        if order.total_value > 10000 and not customer.is_vip():
            raise OrderRequiresApproval()
        order._status = Status.confirmed()  # bezpośredni dostęp do pola
```

**Dlaczego to boli.** Ta sama reguła musi być powtórzona w każdym handlerze który dotyka `Order.status`. Łatwo przeoczyć regułę w nowym handlerze.

**Prawidłowy wzorzec.** Reguła w metodzie domenowej agregatu:

```python
class Order(AggregateRoot[OrderId]):
    def confirm(self, *, customer_is_vip: bool, now: datetime) -> None:
        if self._status != Status.pending():
            raise InvalidStateTransition(...)
        if self.total_value > 10000 and not customer_is_vip:
            raise OrderRequiresApproval(self.id)
        self._status = Status.confirmed()
        self.append_event(OrderConfirmedEvent.now(self.id, now=now))
```

## 6. Dwa lub więcej agregatów w jednej transakcji

**Na czym polega.** Pojedyncza transakcja UoW modyfikuje dwa różne agregaty.

```python
# ŹLE
async with unit_of_work as unit_of_work:
    order = await unit_of_work.orders.get_by_id(order_id)
    inventory = await unit_of_work.inventories.get_by_product_id(product_id)
    order.confirm(now)
    inventory.reserve(order_id, quantity)
    unit_of_work.stage_events(order.pull_events())
    unit_of_work.stage_events(inventory.pull_events())
```

**Dlaczego to boli.**
- Concurrency: dwa agregaty zalockowane w jednej transakcji → deadlock potencjalny
- Granica transakcyjna niejasna — który agregat jest "główny"?
- Przy scaleniu na dwa różne serwisy — nie da się tego zrobić w jednej transakcji

**Prawidłowy wzorzec.** Eventual consistency: pierwszy agregat emituje event, drugi subskrybuje:

```python
# T1: Order
async with unit_of_work as unit_of_work:
    order = await unit_of_work.orders.get_by_id(order_id)
    order.confirm(now)

# T2: Inventory (osobna transakcja, wywołana przez event handler)
async def handle(self, order_confirmed_event: OrderConfirmedEvent):
    async with self._unit_of_work as unit_of_work:
        inventory = await unit_of_work.inventories.get_by_product_id(order_confirmed_event.product_id)
        inventory.reserve(order_confirmed_event.order_id, order_confirmed_event.quantity)
```

## 7. Agregat jako "repozytorium z metodami"

**Na czym polega.** Agregat ma metody typu `find_active_orders()`, `get_orders_by_customer()` albo robi zapytania do bazy.

```python
# ŹLE — agregat robi zapytania
class Customer(AggregateRoot):
    def get_active_orders(self) -> list[Order]: ...  # to nie jest odpowiedzialność agregatu
    def find_orders_by_status(self, status): ...
```

**Dlaczego to boli.** Agregat nie jest repozytorium. Nie ma dostępu do bazy danych. Mieszanie odpowiedzialności.

**Prawidłowy wzorzec.** Agregat zarządza TYLKO swoim stanem. Zapytania → repozytorium/usługa odczytu.

## 8. Agregat jako workaround dla braku JOINów

**Na czym polega.** Agregat jest za duży "bo wtedy nie trzeba robić JOINów w SQL".

```python
# ŹLE — denormalizacja w agregacie zamiast JOINa
class Order(AggregateRoot):
    __slots__ = ("_customer_name", "_customer_email", ...)  # dane klienta skopiowane do order
```

**Dlaczego to boli.** Duplikacja danych. Przy zmianie nazwy klienta wszystkie zamówienia mają starą nazwę. Read model (projekcja) rozwiązuje to lepiej.

**Prawidłowy wzorzec.** Read model z JOINem albo projekcja budowana z eventów dla potrzeb odczytu.

## Szybka checklista przed zatwierdzeniem agregatu

- [ ] Agregat zawiera tylko encje które MUSZĄ być spójne natychmiastowo?
- [ ] Referencje do innych agregatów są wyłącznie przez ID?
- [ ] Wszystkie mutacje stanu idą przez metody domenowe?
- [ ] Żadnych publicznych setterów dla stanu domenowego?
- [ ] Każda metoda mutująca emituje bezwarunkowo event?
- [ ] Agregat zleca zapytania do repository, a sam wyłącznie modeluje stan i interakcje?
- [ ] Pojedyncza transakcja zapisuje dokładnie jeden agregat?
- [ ] Agregat ma optymistyczne blokowanie (`_version`)?
- [ ] Property zwracające kolekcje dają kopie?
- [ ] `__slots__` zadeklarowane (bez `_id`)?
