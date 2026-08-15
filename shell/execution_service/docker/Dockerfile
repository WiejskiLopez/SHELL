FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml ./
COPY shell/ ./shell/
RUN pip install --no-cache-dir -e . && pip install --no-cache-dir uvicorn[standard] aiosqlite
ENV PYTHONUNBUFFERED=1
EXPOSE 8007
CMD ["python", "-m", "shell.execution_service.bootstrap.execution.main", "--host", "0.0.0.0", "--port", "8007", "--db-url", "sqlite+aiosqlite:///shell_dev/execution.db"]
