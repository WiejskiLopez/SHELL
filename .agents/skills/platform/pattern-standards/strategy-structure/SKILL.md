# Strategy Structure

> Reguły struktury wzorca Strategy we wszystkich bounded contextach.

## Definicja

- Strategy pattern — rodzina wymiennych algorytmów, różniących się tylko sposobem wykonania.

## Protokół

- `Protocol` z adnotacją `@runtime_checkable` definiuje kontrakt.

```python
@runtime_checkable
class NodeExecutionStrategy(Protocol):
    @property
    def mode(self) -> str: ...

    async def execute(self, node: Node, context: ExecutionContext) -> NodeResult: ...
```

## Base Strategy

- Wspólna logika dla wszystkich strategii.
- Klasy strategii różnią się tylko wartością `mode`.

```python
class BaseNodeExecutionStrategy:
    def __init__(self, mode: str) -> None:
        self._mode = mode

    @property
    def mode(self) -> str:
        return self._mode

    async def execute(self, node: Node, context: ExecutionContext) -> NodeResult:
        manifest = self._build_manifest(node, context)
        return await self._run(manifest)
```

## Concrete Strategy

- Różni się tylko wartością `mode`.

```python
class AgentStrategy(BaseNodeExecutionStrategy):
    def __init__(self) -> None:
        super().__init__(mode='agent')

class RouterStrategy(BaseNodeExecutionStrategy):
    def __init__(self) -> None:
        super().__init__(mode='router')
```

## Registry

- Strategie są singletonami w rejestrze.
- Registry mapuje `mode` na strategię.

```python
class NodeExecutionStrategyRegistry:
    def __init__(self) -> None:
        self._strategies: dict[str, NodeExecutionStrategy] = {}

    def register(self, strategy: NodeExecutionStrategy) -> None:
        self._strategies[strategy.mode] = strategy

    def get(self, mode: str) -> NodeExecutionStrategy:
        if mode not in self._strategies:
            raise InvalidNodeMode(mode)
        return self._strategies[mode]
```

## Nowa strategia

- Nowy tryb = nowa klasa `*Strategy(mode='nazwa')` + rejestracja w registry.

## Bezstanowość

- Strategie są singletonami — nie dodawaj stanu mutowalnego do strategii.

## Lokalizacja

- `shell/application/<bc>/strategies/<nazwa_strategii>/`
