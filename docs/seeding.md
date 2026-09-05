# Seedowanie danych (dev data) per Bounded Context

Każdy Bounded Context (BC) jest samowystarczalny względem seedowania: sam zasiewa
**swoją** bazę i nie polega na żadnym globalnym orchestratorze. Wspólna platforma
(`shell/platform`) dostarcza wyłącznie neutralny kontrakt — **zero danych, zero
importów BC**.

## Koncepcja

Seedowanie = instancjacja grafu agregatów. Trzy potrzeby korzystają z tego samego
słownika (buildery ORM w seed subpakiecie BC):

| Potrzeba | Kto używa | Co zasiewa |
|---|---|---|
| Dane bazowe / wymagane | `bootstrap_<bc>_database` | schema + dane niezbędne do działania BC (np. base-planner w definition) |
| Dane dev / demo | `seed_<bc>_dev_data` | realistyczne rekordy do lokalnego developmentu |
| Dane testowe | conftesty i testy BC | kontrolowane warianty zbudowane tymi samymi builderami |

Wszystkie seedy są **idempotentne** — można je uruchamiać wielokrotnie; rekordy
wstawiane są tylko gdy ich brakuje.

## Struktura per BC

```
shell/<bc>_service/
├── infrastructure/<bc>/seed/
│   ├── __init__.py   # publiczne API + <Bc>SeedProvider (implementuje SeedProvider)
│   ├── builders.py   # buildery ORM współdzielone z testami
│   ├── base.py       # dane bazowe (opcjonalne; tylko gdzie wymagane)
│   └── dev.py        # dane dev/demo (idempotentne)
└── bootstrap/<bc>/seed.py  # CLI
```

Publiczne API (kontrakt `shell/platform/application/ports/runtime/seed.py` → `SeedProvider`):

```python
async def bootstrap_<bc>_database(url: str, reset_db: bool = False) -> None
async def seed_<bc>_dev_data(url: str) -> None
```

## Uruchamianie

Każdy BC seeduje się sam przez CLI:

```powershell
python -m shell.user_service.bootstrap.user.seed --url sqlite+aiosqlite:///shell/user_service/docker/dev_db/user.db
python -m shell.session_service.bootstrap.session.seed
python -m shell.definition_service.bootstrap.definition.seed
python -m shell.execution_service.bootstrap.execution.seed
python -m shell.scheduling_service.bootstrap.scheduling.seed
python -m shell.project_service.bootstrap.project.seed
python -m shell.ingestion_service.bootstrap.ingestion.seed
```

Bez `--url` używany jest `SHELL_DATABASE_URL` lub adres z `bootstrap/<bc>/config/database_dev.yaml`
(ten sam config co start BC — zero duplikacji). Flaga `--reset-db` dropuje i odtwarza schema
przed seedowaniem, respektując `reset_db` z konfiguracji.

Przy starcie BC (`bootstrap/<bc>/main.py`) dane dev są zasiewane automatycznie,
gdy profil deweloperski ma `seed_dev_data: true` (`shell/config/dev.yaml`).
W prodzie flaga jest `false`.

Demo dane delivery w Ingestion BC nie generują hałasu w runtime: outbox ma
ustawiony `published_at` (relay je pomija), a inbox ma status `PROCESSED`
(worker ich nie zaclaimuje).

## Spójność ID między BC

Bazy BC są osobne (osobne pliki SQLite / schematy). Referencje cross-BC
(np. `workflow.session_id`, `workflow.project_id`) to **nieprzezroczyste stringi**,
bez FK między bazami. Determinystyczna konwencja ID sprawia, że po zasianiu
wszystkich BC rekordy do siebie pasują:

```
dev-<bc>-<entity>-<nazwa>
dev-user-alice, dev-session-alice-1, dev-workflow-simple, dev-project-alpha, ...
```

Pojedynczy BC można zasiewać w izolacji — wiszące referencje do encji z innych BC
są akceptowalne w danych demo.

## Reguły architektoniczne

Egzekwowane przez `shell/tests/architecture/test_seed_topology.py`:

1. Każdy BC musi mieć seed subpakiet z `bootstrap_<bc>_database`,
   `seed_<bc>_dev_data` i providerem `<Bc>SeedProvider`.
2. Seed importuje tylko swój BC oraz `shell.platform` — nigdy innego BC.
3. Globalny `shell.config.seed` został usunięty; żaden import do niego nie wraca.

## Testy

- `shell/tests/<bc>/unit/test_seed.py` — idempotencja: podwójne zasianie nie tworzy duplikatów.
- Conftesty używają `bootstrap_<bc>_database` (dane bazowe) i builderów z `seed/builders.py`.
