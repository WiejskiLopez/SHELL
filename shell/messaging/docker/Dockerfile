FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml ./
COPY shell/ ./shell/
RUN pip install --no-cache-dir -e . && pip install --no-cache-dir uvicorn[standard] aiosqlite
ENV PYTHONUNBUFFERED=1
EXPOSE 8004
CMD ["python", "-m", "shell.messaging.framework.messaging.api", "--host", "0.0.0.0", "--port", "8004", "--db-url", "sqlite+aiosqlite:///shell_dev/messaging.db"]
