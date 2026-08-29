# Bezpieczeństwo transportu między usługami — stan i ścieżka produkcyjna

## Co jest już wdrożone

1. **Auth na wszystkich 7 serwisach** — `AuthMiddleware` wymaga `X-API-Key`
   (albo JWT/sesji dla user) na każdej bramie; `main.py` fail-fast przy braku
   klucza, config w prod wymaga pustego zabronionego klucza.
2. **Podpisane żądania HMAC-SHA256** — `shell/platform/application/authentication/request_signing.py`:
   - klient („podpisujące tokeny") wysyła `X-Shell-Signature` + `X-Shell-Timestamp`
     przy każdym outbound request (`ResilientAsyncClient`, sekret = per-usługa
     `*_SERVICE_API_KEY`);
   - odbiorca (`AuthMiddleware._is_valid_signature`) weryfikuje HMAC(bind
     method+path+timestamp), odrzuca sygnatury starsze niż **300 s** (replay window);
   - zysk nad stałym kluczem: sygnatura jest **short-lived, method- i path-bound**,
     więc przejęcie jednego requestu nie daje tokenu wielokrotnego użytku.
3. Sekrety nie są commitowane (compose'y wymagają env-ów; brak zahardkodowanych
   haseł w repo).

## Pozostaje przed produkcją (decyzja wg modelu ryzyka)

### 0. Server-side TLS / mTLS — przygotowane w kodzie, **konfiguracja przyszłościowa (wyłączona)**
- Scaffolding istnieje w `shell/platform/framework/bootstrap/server.py`:
  każdy `main.py` buduje uvicorn config przez `build_service_uvicorn_config`.
- Po ustawieniu zmiennych `{SERVICE}_SERVICE_TLS_CERTFILE` + `_KEYFILE` serwer
  uruchamia się z TLS; dodanie `_CA_CERTS` weryfikuje certyfikat klienta
  (optional), a `_REQUIRE_CLIENT_CERT=true` wymusza mTLS (`CERT_REQUIRED`).
- Domyślnie **żadna zmienna nie jest ustawiona** ⇒ serwer działa jak dziś
  (HTTP za edge/mesh). Bez realnego CA i wydanych certyfikatów ten path pozostaje
  wyłączony — to celowo „future configuration".

### A. mTLS (najsilniejszy) — gdy usługi w tym samym środowisku/meshu
- Certyfikaty per-usługa (np. SPIFFE/SPIRE, Vault PKI albo Istio/Envoy),
  rotacja, CRL/SCEP; wymuszenie na warstwie transportu (mesh sidecar albo proxy).
- HMAC może zostać wyłączony lub działa równolegle (defense in depth).
- Wymaga: infrastruktury CA + mesh; koszt operacyjny najwyższy.

### B. Podpisane tokeny (JWT z `iss`/`aud`/`exp`, secret per-usługa) — zalecane minimum
- Zamiast `X-API-Key` wysyłać service-token: `X-Shell-Service` + `Authorization: Bearer <JWT>`.
- Firma kluczy per-usługa (nie wspólny), `iss=execution`, `aud=definition` itd.
- Aktualny HMAC z `request_signing.py` może pozostać jako warstwa antreplay na
  istniejących kluczach do czasu migration.

### C. Secrets management
- Klucze/sekrety w Vault/env-based secrets, nie w compose/env pliku w repo.
- Rotacja wg harmonogramu; monitoring użycia po metrykach auth (401/403 ratio).

## Staging rollout (kolejność)

1. Wdrożyć obraz z metrykami (`/metrics`) + `/readiness` w healthcheckach.
2. Włączyć Prometheus scrape + reguły z `docs/metrics/alerts.yml`; dashboard z
   `docs/metrics/dashboard.json`.
3. Kalibrować SLO (patrz `docs/metrics/sli-slo.md`) — dostroić progi alertów.
4. Włączyć service-tokeny (opcja B), wyłączyć fallback API-key po pełnym
   pokryciu ruchu.
5. Dopiero potem: mTLS (opcja A) w docelowym środowisku/meshu, jeśli wymagany.

## Dokumentacja decyzyjna

- `docs/metrics/sli-slo.md` — SLI/SLO, error budget.
- `docs/metrics/alerts.yml` — reguły Prometheus.
- `docs/metrics/dashboard.json` — Grafana dashboard.
- `shell/platform/framework/bootstrap/server.py` — przygotowany scaffolding
  TLS/mTLS (konfiguracja przyszłościowa, domyślnie wyłączona).