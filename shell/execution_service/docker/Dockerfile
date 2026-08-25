FROM python:3.11-slim AS platform-builder
WORKDIR /build
ARG SOURCE_DATE_EPOCH=0
ENV SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH
COPY packaging/shell-platform/pyproject.toml ./pyproject.toml
COPY shell/platform ./shell/platform
RUN python -m pip wheel --no-cache-dir --no-deps --wheel-dir /dist .

FROM python:3.11-slim AS execution-service-builder
WORKDIR /build
ARG SOURCE_DATE_EPOCH=0
ENV SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH
COPY packaging/shell-execution-service/pyproject.toml ./pyproject.toml
COPY shell/execution_service ./shell/execution_service
RUN python -m pip wheel --no-cache-dir --no-deps --wheel-dir /dist .

FROM python:3.11-slim
WORKDIR /app
COPY --from=platform-builder /dist /tmp/wheels
COPY --from=execution-service-builder /dist /tmp/wheels
RUN pip install --no-cache-dir /tmp/wheels/*.whl && rm -rf /tmp/wheels
ENV PYTHONUNBUFFERED=1
EXPOSE 8007
CMD ["python", "-m", "shell.execution_service.bootstrap.execution.main", "--host", "0.0.0.0", "--port", "8007"]
