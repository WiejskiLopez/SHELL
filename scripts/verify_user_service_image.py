#!/usr/bin/env python
"""Run the User service image and verify its standalone HTTP surface."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_SERVICE_SPECS: dict[str, dict[str, str | int]] = {
    "definition": {
        "port": 8002,
        "prefix": "DEFINITION_SERVICE",
        "worker_module": "shell.definition_service.bootstrap.definition.main",
        "route": "/api/v1/graph-definitions/{graph_definition_id}",
    },
    "execution": {
        "port": 8007,
        "prefix": "EXECUTION_SERVICE",
        "worker_module": "shell.execution_service.bootstrap.execution.main",
        "route": "/api/v1/workflows",
    },
    "ingestion": {
        "port": 8004,
        "prefix": "INGESTION_SERVICE",
        "worker_module": "shell.ingestion_service.bootstrap.ingestion.main",
        "route": "/api/v1/ingestions/",
    },
    "project": {
        "port": 8005,
        "prefix": "PROJECT_SERVICE",
        "worker_module": "shell.project_service.bootstrap.project.main",
        "route": "/api/v1/projects",
    },
    "scheduling": {
        "port": 8006,
        "prefix": "SCHEDULING_SERVICE",
        "worker_module": "shell.scheduling_service.bootstrap.scheduling.main",
        "route": "/api/v1/scheduler-definitions/",
    },
    "session": {
        "port": 8003,
        "prefix": "SESSION_SERVICE",
        "worker_module": "shell.session_service.bootstrap.session.main",
        "route": "/api/v1/sessions",
    },
    "user": {
        "port": 8001,
        "prefix": "USER_SERVICE",
        "worker_module": "shell.user_service.bootstrap.user.main",
        "route": "/api/v1/users/",
    },
}


def _docker(*arguments: str) -> str:
    result = subprocess.run(
        ["docker", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def _request(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, str] | None = None,
    api_key: str | None = None,
) -> tuple[int, dict[str, object]]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=body,
        method=method,
        headers={"Content-Type": "application/json"}
        | ({"X-API-Key": api_key} if api_key is not None else {}),
    )
    try:
        with urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read())
    except HTTPError as error:
        return error.code, json.loads(error.read())


def verify_image(image: str, service: str) -> None:
    if service not in _SERVICE_SPECS:
        raise ValueError(f"Unknown service: {service}")
    spec = _SERVICE_SPECS[service]
    container_name = f"shell-{service}-image-check"
    worker_name = f"{container_name}-worker"
    rabbit_name = f"{container_name}-rabbit"
    network_name = f"{container_name}-network"
    volume_name = f"{container_name}-volume"
    service_prefix = spec["prefix"]
    worker_module = spec["worker_module"]
    assert isinstance(worker_module, str)
    container_port = str(spec["port"])
    database_url = f"sqlite+aiosqlite:////tmp/{service}.db"
    for resource in (container_name, worker_name, rabbit_name):
        subprocess.run(
            ["docker", "rm", "--force", resource],
            check=False,
            capture_output=True,
            text=True,
        )
    subprocess.run(["docker", "network", "create", network_name], check=False)
    subprocess.run(["docker", "volume", "create", volume_name], check=False)
    try:
        _docker(
            "run",
            "--detach",
            "--name",
            rabbit_name,
            "--network",
            network_name,
            "--env",
            "RABBITMQ_DEFAULT_USER=shell",
            "--env",
            "RABBITMQ_DEFAULT_PASS=shell",
            "rabbitmq:3-alpine",
        )
        for _ in range(60):
            rabbit_logs = subprocess.run(
                ["docker", "logs", rabbit_name],
                check=False,
                capture_output=True,
                text=True,
            )
            if "Server startup complete" in rabbit_logs.stdout + rabbit_logs.stderr:
                break
            time.sleep(1)
        else:
            raise RuntimeError("RabbitMQ did not become ready")

        _docker(
            "run",
            "--detach",
            "--name",
            container_name,
            "--network",
            network_name,
            "--volume",
            f"{volume_name}:/tmp",
            "--publish",
            f"0:{container_port}",
            "--env",
            f"{service_prefix}_DATABASE_URL={database_url}",
            "--env",
            f"{service_prefix}_BROKER_URL=amqp://invalid:invalid@127.0.0.1:5672",
            "--env",
            f"{service_prefix}_API_KEY=pilot-test-key",
            image,
        )
        published_port = _docker("port", container_name, f"{container_port}/tcp")
        port_match = re.search(r":(\d+)$", published_port)
        if port_match is None:
            raise RuntimeError(f"Could not determine published port: {published_port}")
        base_url = f"http://127.0.0.1:{port_match.group(1)}"

        for _ in range(30):
            try:
                health_status, health_body = _request(f"{base_url}/health")
                if health_status == 200:
                    break
            except (ConnectionError, TimeoutError, URLError):
                time.sleep(1)
        else:
            raise RuntimeError("User service did not become healthy")

        assert health_body["status"] == "ok"
        readiness_status, readiness_body = _request(
            f"{base_url}/readiness",
            api_key="pilot-test-key",
        )
        assert readiness_status == 503
        assert readiness_body["status"] == "not_ready"
        assert "checks" in readiness_body

        _docker(
            "run",
            "--detach",
            "--name",
            worker_name,
            "--network",
            network_name,
            "--volume",
            f"{volume_name}:/tmp",
            "--env",
            f"{service_prefix}_DATABASE_URL={database_url}",
            "--env",
            f"{service_prefix}_BROKER_URL=amqp://shell:shell@{rabbit_name}:5672",
            "--env",
            f"{service_prefix}_API_KEY=pilot-test-key",
            image,
            "python",
            "-m",
            worker_module,
            "--worker",
        )

        for _ in range(30):
            readiness_status, readiness_body = _request(
                f"{base_url}/readiness",
                api_key="pilot-test-key",
            )
            if readiness_status == 200:
                break
            time.sleep(1)
        else:
            raise RuntimeError(f"{service} worker did not make readiness ready: {readiness_body}")
        assert readiness_body["status"] == "ready"

        api_status, api_body = _request(
            f"{base_url}/openapi.json",
            api_key="pilot-test-key",
        )
        assert api_status == 200, api_body
        paths = api_body.get("paths")
        assert isinstance(paths, dict)
        route = spec["route"]
        assert isinstance(route, str)
        assert route in paths
    finally:
        logs = subprocess.run(
            ["docker", "logs", container_name],
            capture_output=True,
            text=True,
        )
        if logs.stdout:
            print(logs.stdout)
        if logs.stderr:
            print(logs.stderr)
        for resource in (container_name, worker_name, rabbit_name):
            subprocess.run(
                ["docker", "rm", "--force", resource],
                check=False,
                capture_output=True,
                text=True,
            )
        subprocess.run(["docker", "network", "rm", network_name], check=False)
        subprocess.run(["docker", "volume", "rm", volume_name], check=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--service", choices=tuple(_SERVICE_SPECS), default="user")
    args = parser.parse_args()
    verify_image(args.image, args.service)


if __name__ == "__main__":
    main()