FROM python:3.14-slim AS platform-builder

WORKDIR /build
ARG SOURCE_DATE_EPOCH=0
ENV SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH
COPY packaging/shell-platform/pyproject.toml ./pyproject.toml
COPY shell/platform ./shell/platform
RUN python -m pip wheel --no-cache-dir --no-deps --wheel-dir /dist .

FROM python:3.14-slim AS definition-service-builder
WORKDIR /build
ARG SOURCE_DATE_EPOCH=0
ENV SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH
COPY packaging/shell-definition-service/pyproject.toml ./pyproject.toml
COPY shell/definition_service ./shell/definition_service
RUN python -m pip wheel --no-cache-dir --no-deps --wheel-dir /dist .

FROM python:3.14-slim AS certificate-builder
WORKDIR /certificates
ARG CERTIFICATE_BUILD_ID=local
COPY shell/certificates ./shell/certificates
COPY shell/certs/ca.crt shell/certs/ca.key ./ca/
RUN python -m pip install --no-cache-dir cryptography
RUN echo "certificate-build=$CERTIFICATE_BUILD_ID" && python -m shell.certificates issue --ca-dir /certificates/ca --output-dir /generated --name definition --hostname shell-definition-api

FROM python:3.14-slim

WORKDIR /app

COPY --from=platform-builder /dist /tmp/wheels
COPY --from=certificate-builder /generated/ca.crt /run/secrets/shell-mtls/ca.crt
COPY --from=certificate-builder /generated/definition.crt /run/secrets/shell-mtls/definition.crt
COPY --from=certificate-builder /generated/definition.key /run/secrets/shell-mtls/definition.key
COPY --from=definition-service-builder /dist /tmp/wheels
RUN pip install --no-cache-dir /tmp/wheels/*.whl && rm -rf /tmp/wheels

ENV PYTHONUNBUFFERED=1

EXPOSE 8002

CMD ["python", "-m", "shell.definition_service.bootstrap.definition.main", "--host", "0.0.0.0", "--port", "8002"]
