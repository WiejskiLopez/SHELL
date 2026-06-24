# Entity Structure

> Reguły struktury klasy Entity we wszystkich bounded contextach.

## Dziedziczenie

- Każda encja dziedziczy po `Entity[TId]` z platformy.
- `TId` to konkretny Value Object identyfikatora encji.

```python
class Node(Entity[NodeId]):
    ...
```

## Klasa

- **Nie używać `@dataclass`** dla encji — tożsamość to nie równość strukturalna.
- Obowiązkowo `__slots__` ze wszystkimi polami. Nie powtarzać `_id` (dziedziczony z `Entity`).

```python
class Node(Entity[NodeId]):
    __slots__ = ('_name', '_type', '_config')

    def __init__(self, node_id: NodeId, name: NodeName, type_: NodeType, config: NodeConfig) -> None:
        super().__init__(node_id)
        self._name = name
        self._type = type_
        self._config = config
```

## Tożsamość

- `__eq__` i `__hash__` bazują wyłącznie na ID — nigdy na stanie.
- ID jest niemutowalne po utworzeniu — brak settera dla `_id`.

```python
def __eq__(self, other: object) -> bool:
    if not isinstance(other, Node):
        return NotImplemented
    return self._id == other._id

def __hash__(self) -> int:
    return hash(self._id)
```

## Stan

- Stan encji modyfikowalny wyłącznie przez metody domenowe.
- Żadnych publicznych setterów. Żadnych mutowalnych referencji przez property.
- Property zwracające kolekcje zwracają kopie.

```python
@property
def name(self) -> NodeName:
    return self._name

@property
def config(self) -> NodeConfig:
    return self._config  # NodeConfig to immutable VO
```

## Factory methods

- Encje mogą mieć statyczne `@classmethod` factory methods zamiast bezpośredniego konstruktora, jeśli tworzenie wymaga logiki biznesowej.

```python
@classmethod
def create_router(cls, name: NodeName, config: RouterConfig) -> Node:
    return cls(NodeId.generate(), name, NodeType.ROUTER, config)
```

## Status

- Stany encji to `StrEnum` dziedziczący po `ValueObject`.

```python
class NodeStatus(StrEnum):
    IDLE = 'idle'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
```

## Encje dziecięce

- Mają lokalną tożsamość tylko w kontekście rodzica.
- Modyfikowane wyłącznie przez metody Aggregate Root.
- Nie mają własnego repozytorium.

## Lokalizacja

- `shell/domain/<bc>/aggregates/<nazwa_agregatu>/entities/`
- Encje współdzielone między agregatami: `shell/domain/<bc>/entities/`

## Bezpieczeństwo

- Encje to czysty kod domenowy.
- Brak importów ORM, brak adnotacji serializacyjnych, brak zależności od `shell.infrastructure.*`.
