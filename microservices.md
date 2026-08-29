# Ocena gotowości platformy SHELL do prawdziwych mikroserwisów enterprise

Status: **analiza + weryfikacja u źródła**. Każda uwaga jest poparta ścieżką
i numerem linii kodu.

## Werdykt

Platforma to obecnie **modularny monolit / distributed monolith** — nie zespół
niezależnie wdrażalnych mikroserwisów. Warstwa **logiczna** (bounded contexts,
DDD, CQRS, outbox/inbox, import-linter) jest zbudowana wzorowo, ale na poziomie
**artefaktu, infra, configu, bezpieczeństwa i operacji** brakuje niemal
wszystkiego, co definiuje mikroserwisy enterprise. Poniżej uszeregowane luki,
wszystkie potwierdzone kodem.

---

## 1. Jeden pakiet Pythona zawiera wszystkie serwisy (brak niezależnej paczkowania)

- **Problem:** istnieje dokładnie **jeden** `pyproject.toml` (root repo), który
  build'uje **jeden** pakiet `shell` obejmujący `platform` + wszystkie 7 serwisów.
  Brak `pyproject.toml`/`requirements*.txt` per-serwis (zweryfikowano: w całym repo
  jest tylko `C:\Users\palysiewicz\IdeaProjects\SHELL\pyproject.toml`).
- **Dowód:** `pyproject.toml:38-40` → `[tool.setuptools.packages.find] include = ["shell*"]`.
- **Dowód (Docker):** każdy `Dockerfile` kopiuje całe `shell/` i robi `pip install -e .`:
  `shell/definition_service/docker/Dockerfile:5-8`, analogicznie w `execution`, `user` itd.
  Różni się tylko `CMD`. Wszystkie obrazy budowane są ze wspólnego `context: ../../..`.
- **Skutek:** nie da się wdrożyć jednego serwisu bez pozostałych; zmiana zależności
  lub wersji pakietu dotyka wszystkie serwisy naraz.
- **Uzasadnienie (realny problem):** dla mikroserwisów każdy usługa musi być
  niezależnie wersjonowanym, publikowanym i wdrażanym artefaktem. Tu istnieje
  jeden wspólny wheel i jeden `uv.lock`.

---

## 2. Współdzielony, monolitowy kernel `shell.platform` — silne sprzężenie

- **Problem:** każdy serwis importuje masowo z `shell.platform` (szacunkowo
  81–694 importy na serwis). `platform` zawiera persistence, messaging, serializację,
  config, API middleware, identity, logging itd.
- **Dowód:** `shell/session_service/bootstrap/session/container/session_core_container.py`
  importuje `shell.platform.infrastructure.messaging.transport.rabbit`,
  `shell.platform.infrastructure.persistence.sql`, `shell.platform.infrastructure.configuration.shell_config`.
  Ten sam wzorzec w każdym `*_core_container.py`.
- **Skutek:** zmiana w `platform/` ripple'uje do wszystkich serwisów. Nie ma
  osobno wersjonowanej dystrybucji `shell-platform` jako stabilnej biblioteki-kontraktu.
- **Uzasadnienie:** nie jest sam w sobie błędem mieć shared kernel, ale w
  mikroserwisach musi być to **stabilny, niezależnie wersjonowany kontrakt**,
  a nie współdzielony kod źródłowy, na którym każdy serwis jest skalany.

---

## 3. Prawdziwe sprzężenie kodu między BC: `session_service → user_service`

- **Problem:** `session_service` importuje klasę bezpośrednio z `user_service`
  (poziom Python), a nie przez sieć/wire-contract.
- **Dowody (grep — 3 wystąpienia):**
  - `shell/session_service/bootstrap/session/event_registry.py:16`
  - `shell/session_service/bootstrap/session/container/session_core_container.py:283`
  - `shell/session_service/application/session/session/event_handlers/auth_session_created_event_handler.py:33`
  `from shell.user_service.application.user.auth_session.integration_events.auth_session_created_integration_event import ...`
- **Skutek:** dwa „mikroserwisy" są połączone w Pythonie; nie da się ich ze sobą
  wdrożyć niezależnie. Test architektury **świadomie to dozwala**:
  `shell/tests/architecture/..._ALLOWED_CROSS_BC` zawiera
  `shell.user_service.application.user.auth_session.integration_events`.
- **Uzasadnienie:** dla mikroserwisów integracja musi iść wyłącznie przez
  zdarzenie na brokerze lub HTTP z kontraktem DTO, nie przez import klas.

---

## 4. Config współdzielony, nie izolowany per-serwis

- **Problem:** jeden wspólny katalog config + jedna globalna konfiguracja dla
  wszystkich serwisów; brak per-serwis katalogów config (zweryfikowano: żaden
  `*_service` nie ma własnego `config/`).
- **Dowód:** `shell/platform/infrastructure/configuration/shell_config.py:24-26` →
  `_config_dir()` = `Path(__file__).resolve().parents[3] / "config"` — pojedynczy
  katalog. `shell/config/` zawiera tylko `default.yaml`, `dev.yaml`, `prod.yaml`.
- **Dowód:** `shell_config.py:86` → jedna `broker_url: amqp://shell:shell@localhost:5672`.
  `SHELL_DATABASE_URL`, `SHELL_API_KEY`, `SHELL_EVENTS_BROKER_URL` są współdzielone.
- **Dowód:** `shell_config.py:116` → jeden globalny `SHELL_PROFILE` (dev/prod)
  dla WSZYSTKICH serwisów naraz — nie da się mieć jednego serwisu w dev, a innego
  w prod.
- **Dowód (compose):** każdy compose montuje ten sam katalog `./config:/app/config`
  (np. `shell/execution_service/docker/docker-compose.yml:22,43`).
- **Skutek:** podział DB to tylko runtime `--db-url` (np. `execution.db`), nie
  prawdziwa separacja konfiguracji; jeden API key / broker URL / profil globalny.
- **Uzasadnienie:** w mikroserwisach config/sekrety są per-usługa (namespaced env,
  wydzielone secrets), a nie jeden wspólny profil dla platformy.

---

## 5. Brak platformy serwisowej: gateway / service discovery / mesh

- **Problem:** brak API gatewaya, rejestru usług, load balancingu,
  Kubernetes/Consul/Istio/Envoy.
- **Dowód (grep):** brak jakichkolwiek odniesień do `consul|istio|envoy|kubernetes|k8s`
  w kodzie. `create_api_discovery_router` (`shell/platform/framework/api/setup.py:122-128`)
  tylko **listuje wersje API** (`.list_versions()`), to NIE jest registry usług.
- **Dowód (compose):** wszystkie serwisy lecą na jednej współdzielonej sieci
  `shell-net` — `shell/execution_service/docker/docker-compose.yml:51-52`,
  analogicznie we wszystkich pozostałych. Serwisy wołają się po twardych ścieżkach
  `/api/v1/...` opartych o hostname sieci, bez DNS-discovery i bez routingu.
- **Skutek:** brak niezależnego skalowania, zero-trust, observability na granicy,
  canary/blue-green na poziomie usług.
- **Uzasadnienie:** gateway + discovery + mesh to rdzeń architektury mikroserwisowej;
  ich brak czyni to nadal monolitem uruchamianym jako osobne procesy.

---

## 6. Brak odporności (resilience) na ścieżce HTTP między serwisami

- **Problem:** cross-BC wywołania HTTP nie mają **timeoutu, retry ani circuit breakera**,
  ani nawet propagacji correlation-id.
- **Dowody:**
  - `shell/execution_service/infrastructure/execution/graph_execution/adapters/graph_definition/graph_definition_provider_http_adapter.py:36,49`
    → gołe `await self._client.get/post(...)`, brak `timeout=`, brak retry/circuit.
  - `shell/execution_service/infrastructure/execution/session_execution/adapters/session_query_provider/session_query_provider_http_adapter.py:31`
    → identycznie.
  - Brak libki circuit-breaker (grep `pybreaker|circuitbreaker` → brak wyników).
  - `CorrelationIdAsyncClient` (`shell/platform/infrastructure/context/client.py`) istnieje,
    ale grep nie znajduje go wpiętego w te adaptery.
- **Kontrast:** warstwa messagingowa jest odporna (backoff, DLQ, lease, heartbeat,
  idempotencja) — ale HTTP jest nagie.
- **Uzasadnienie:** w mikroserwisach awaria zależnej usługi nie może zawiesić
  wywołującego; brak timeoutu/retry/breaker = awarie kaskadowe, brak graceful
  degradation.

---

## 7. Luki bezpieczeństwa: nieuwierzytelnione API i zahardkodowane sekrety

- **Problem A — auth tylko na user_service:** `AuthMiddleware` jest zamontowany
  wyłącznie w `shell/user_service/framework/user/api/app.py`. **Execution i Definition
  nie mają żadnego autha.**
- **Dowód:** `shell/execution_service/framework/execution/api/app.py:53-54` → tylko
  `CorrelationIdMiddleware` + `domain_error_handler`, **bez** `AuthMiddleware`.
  Grep `AuthMiddleware|api_key` w `execution_service/framework` i
  `definition_service/framework` → **0 wyników**.
- **Problem B — zahardkodowane sekrety w commitowanych plikach:**
  - `shell/rabbitmq/docker/docker-compose.yml:9-10` → `RABBITMQ_DEFAULT_USER: shell`,
    `RABBITMQ_DEFAULT_PASS: shell`.
  - `shell/*/docker/docker-compose.yml:10` → `SHELL_EVENTS_BROKER_URL: amqp://shell:shell@rabbitmq`
    (np. execution, definition, user).
  - `shell/platform/infrastructure/configuration/shell_config.py:86` → domyślny
    `broker_url = "amqp://shell:shell@localhost:5672"` w kodzie.
  - `user_service` compose → `--api-key dev-user-key`.
- **Uzasadnienie:** nieuwierzytelnione API = pełny dostęp do danych/wykonywania
  bez uprawnień; sekrety w repo = kompromitacja na starcie. JWT `secure=False` i
  pusty domyślny secret dodatkowo osłabiają user_service w kontenerze.

---

## 8. Migracje: `create_all` zamiast versioned migrations (Alembic)

- **Problem:** brak zmigrowanych, wersjonowanych migracji. Każde uruchomienie
  serwisu robi `metadata.create_all()`.
- **Dowody (grep `create_all` — 7 plików produkcyjnych):**
  - `shell/user_service/migrations/baseline.py:65`
  - `shell/scheduling_service/migrations/baseline.py:58`
  - `shell/session_service/migrations/baseline.py:51`
  - `shell/execution_service/migrations/baseline.py:58`
  - `shell/project_service/migrations/baseline.py:53`
  - `shell/definition_service/migrations/baseline.py:65`
  - `shell/ingestion_service/migrations/baseline.py:45`
- **Dowód:** `alembic.ini` wskazuje na `platform/infrastructure/persistence/migrations/sql`
  — **katalog nie istnieje** (brak `.../versions/`, potwierdzone `Test-Path` = False).
- **Dowód wewnętrzny:** `docs/inbox-outbox-architecture.md:269` sam ostrzega, że w
  produkcji trzeba stosować migracje schematu, a nie `create_all`.
- **Skutek:** `create_all` nie ewoluuje schematu (brak `ALTER TABLE`), nie da się
  bezpiecznie aktualizować bazy produkcyjnej z istniejącymi danymi; brak
  per-service wersjonowania schematu.
- **Uzasadnienie:** w enterprise każda usługa ma własną, wersjonowaną ścieżkę
  migracji, wdrażaną przed/at-górze procesu niezależnie od innych serwisów.

---

## 9. Brak prawdziwej observability: tracing i metryki

- **Problem A — brak distributed tracing (OpenTelemetry):** jedynie korelacja na
  poziomie aplikacji (correlation/causation), brak span/trace ID.
- **Problem B — brak metryk (Prometheus `/metrics`):** backend metryk to
  **headless placeholder** logujący do pliku.
- **Dowody:**
  - Grep `opentelemetry|prometheus|pybreaker|circuitbreaker|consul|istio|envoy|kubernetes`
    w `shell/**/*.py` → **0 trafień technologicznych** (tylko komentarze).
  - `shell/platform/observability/infrastructure/metrics/logging_metrics_backend.py:1-17` →
    „dependency-free MetricsBackend ... used until a real backend (Prometheus,
    etc.) is wired". Każdy `*_core_container.py` rejestruje `LoggingMetricsBackend`
    (np. `execution_core_container.py:326`).
  - Brak endpointu `/metrics` (grep → tylko `/health` i `/readiness`).
- **Uzasadnienie:** bez OTel tracingu i metryk nie da się diagnozować
  rozproszonych żądań, robić SLO/SLI, alertować o backlogu/wydajności per-usługa.

---

## 10. Readiness vs liveness i krycie prawdziwej zależności (broker)

- **Problem:** podział `/health` (liveness) vs `/readiness` (503 + diagnostyka)
  istnieje i jest dobrze zaprojektowany, ALE (a) orchestrator nie używa `/readiness`,
  (b) readiness nie sprawdza RabbitMQ — realnej zależności.
- **Dowody:**
  - `/readiness` mount'owany: `shell/platform/observability/framework/api/readiness.py:18-32`,
    `shell/platform/observability/framework/api/health.py:15-24`; `SQLReadinessProbe`
    `shell/platform/observability/infrastructure/health/sql_readiness_probe.py:56-71`.
  - `SQLReadinessProbe` sprawdza tylko: `database` (`SELECT 1`),
    `migrations`, `worker`, `backlog` — **brak sprawdzenia brokera** (`observability/infrastructure/health/sql_readiness_probe.py:56-136`).
  - Healthchecki w każdym compose wołają tylko `/health` (np.
    `shell/execution_service/docker/docker-compose.yml:13-18`), więc orchestrator
    nie może gatingować ruchu po readiness.
- **Skutek:** usługa może być „ready" mimo martwego brokera; orchestrator nie
  wycofuje ruchu z niegotowej repliki.
- **Uzasadnienie:** readiness powinien uwzględniać krytyczne zależności (DB + broker),
  a orchestration (K8s/Swarm) powinno używać `/readiness` do drążenia ruchu.

---

## Podsumowanie — co jest mocne (nie wymaga poprawy)

- **Transactional Outbox / Inbox** — wzorcowe: atomowy zapis zmiany+outbox+ack,
  publisher confirms, idempotent inbox (`ON CONFLICT`), dedup store,
  DLQ + retention, lease/heartbeat, backoff z jitterem. (potwierdzone w
  `shell/platform/infrastructure/messaging/**`).
- **Dyscyplina architektoniczna** — import-linter, testy AST, CQRS, mypy strict,
  symetryczne round-trip mappery, izolacja przez duplicated ID VOs.
- **Logowanie strukturalne JSON + korelacja/causation przez Rabbit i HTTP.**

---

## Priorytetowa ścieżka do prawdziwych mikroserwisów enterprise

1. **Rozbić pakiet** → osobne paczki per-serwis + `shell-platform` jako
   osobno wersjonowana biblioteka; per-service lockfile/zależności.
2. **Przenieść `session→user` na wire** → pozbyć się importu Python na rzecz
   eventu/HTTP z kontraktem DTO.
3. **Gateway + service discovery** (np. Traefik/Consul) zamiast twardych ścieżek
   na wspólnej sieci `shell-net`.
4. **Auth na wszystkich serwisach** (JWT/API-key) + sekrety z Vault/env, nie z compose.
5. **Versioned Alembic migrations** per-usługa zamiast `create_all`.
6. **Retry / circuit-breaker / timeout + correlation** na wszystkich cross-BC
   HTTP adapterach (uzyć `CorrelationIdAsyncClient`).
7. **OTel tracing + Prometheus `/metrics`**; użyć `/readiness` w healthcheckach
   orchestratora i rozszerzyć probe o broker.
8. **Config per-serwis** — namespaced env, per-service profile/secrets,
   własna izolacja bazy/configu.
