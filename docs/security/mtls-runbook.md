# Runbook: mTLS z certyfikatem per obraz (research/dev)

## Model (zgodny z implementacją Dockerfile)

Każdy obraz usługi (`definition`, `session`, `execution`) ma **swój** certyfikat
podpisany przez CA w stage `certificate-builder` podczas budowania. Finalny obraz
zawiera tylko `ca.crt` (publiczny CA) + `…crt`/`…key` danej usługi, w katalogu
`/run/secrets/shell-mtls/`. Klucz prywatny CA (`ca.key`) jest używany tylko przy
budowie (maszyna buildowa / repo) i nie trafia do obrazu.

Obraz jest **samowystarczalny**: po wgraniu do Nexus i odpaleniu na dowolnym
hoście z Dockerem działa bez dociągania certyfikatów.

## Zależność temperalna

- Rotacja przebudową: certyfikaty ważne **1 rok** (generator default 365 dni);
  przebudowa przed końcem okna odświeża certy. Okresowo odświeżaj też CA (5 lat).
- Aby każda przebudowa dała **świeży** cert, buduj z unikalnym
  `CERTIFICATE_BUILD_ID` (łamie warstwę certyfikatu):
  ```powershell
  $env:CERTIFICATE_BUILD_ID = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
  docker compose -f shell/mtls-demo/docker-compose.yml build
  ```

## Build + push do Nexus (przykład dla definition)

```powershell
# 1. (opcjonalnie) wygeneruj/odśwież CA w repo — build-stage sam wydaje certy per obraz
./scripts/generate_mtls_certs.py --output-dir shell/certs --force

# 2. build z unikalnym ID certyfikatu
docker build --build-arg CERTIFICATE_BUILD_ID=$(date +%s) `
  -f shell/definition_service/docker/Dockerfile -t registry/nexus/shell-definition:mtls .

# 3. wgraj do Nexus
docker push registry/nexus/shell-definition:mtls
```

## Uruchomienie na dowolnym hoście (przykład)

```powershell
docker compose -f shell/mtls-demo/docker-compose.yml up -d
```

Compose jedynie ustawia env (URL-e, klucze) i włącza mTLS wskazując wbudowane
ścieżki `/run/secrets/shell-mtls/…` — **nie montuje żadnych certyfikatów z hosta**.

## Weryfikacja ręczna

Klient z własnym certem (tożsamość per usługa):

```powershell
curl.exe --cacert shell/certs/ca.crt `
  --cert shell/certs/execution.crt --key shell/certs/execution.key `
  https://localhost:8442/api/v1/graph-definitions/base-planner-id
```

Klient bez certu → brak odpowiedzi / zerwanie połączenia (mTLS wymuszony).

Weryfikacja po stronie klienta wewnętrznego (execution→definition) jest już
zaimplementowana (`ResilientAsyncClient` + `tls_identity="execution"` czyta
`EXECUTION_SERVICE_MTLS_*`).

## Znane ograniczenia tego badanego zestawu

- Brak autoryzacji po tożsamości (CN) — dalszy krok.
- Rotacja przez przebudowę (1 rok); brak Vault/HSM.
- mTLS obejmuje HTTP między usługami; broker (RabbitMQ) poza zakresem.
- W pełnej produkcji preferowany service mesh / SPIFFE z certymentem na runtime.