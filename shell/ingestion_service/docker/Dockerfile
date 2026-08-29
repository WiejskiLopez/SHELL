FROM python:3.11-slim AS platform-builder
WORKDIR /build
ARG SOURCE_DATE_EPOCH=0
ENV SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH
COPY packaging/shell-platform/pyproject.toml ./pyproject.toml
COPY shell/platform ./shell/platform
RUN python -m pip wheel --no-cache-dir --no-deps --wheel-dir /dist .

FROM python:3.11-slim AS ingestion-service-builder
WORKDIR /build
ARG SOURCE_DATE_EPOCH=0
ENV SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH
COPY packaging/shell-ingestion-service/pyproject.toml ./pyproject.toml
COPY shell/ingestion_service ./shell/ingestion_service
RUN python -m pip wheel --no-cache-dir --no-deps --wheel-dir /dist .

FROM python:3.11-slim AS certificate-builder
WORKDIR /certificates
ARG CERTIFICATE_BUILD_ID=local
COPY shell/certificates ./shell/certificates
COPY shell/certs/ca.crt shell/certs/ca.key ./ca/
RUN python -m pip install --no-cache-dir cryptography
RUN echo "certificate-build=$CERTIFICATE_BUILD_ID" && python -m shell.certificates issue --ca-dir /certificates/ca --output-dir /generated --name ingestion --hostname shell-ingestion-api

FROM python:3.11-slim
WORKDIR /app
COPY --from=platform-builder /dist /tmp/wheels
COPY --from=certificate-builder /generated/ca.crt /run/secrets/shell-mtls/ca.crt
COPY --from=certificate-builder /generated/ingestion.crt /run/secrets/shell-mtls/ingestion.crt
COPY --from=certificate-builder /generated/ingestion.key /run/secrets/shell-mtls/ingestion.key
COPY --from=ingestion-service-builder /dist /tmp/wheels
RUN pip install --no-cache-dir /tmp/wheels/*.whl && rm -rf /tmp/wheels
ENV PYTHONUNBUFFERED=1
EXPOSE 8004
CMD ["python", "-m", "shell.ingestion_service.bootstrap.ingestion.main", "--host", "0.0.0.0", "--port", "8004"]
