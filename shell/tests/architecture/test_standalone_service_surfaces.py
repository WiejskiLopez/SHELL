"""Architecture tests for independently deployable bounded contexts."""

from __future__ import annotations

from _arch_helpers import BASE

_BCS = (
    "definition_service",
    "execution_service",
    "ingestion_service",
    "project_service",
    "scheduling_service",
    "session_service",
    "user_service",
)


def test_each_bc_has_an_independent_service_surface() -> None:
    missing: list[str] = []

    for bounded_context in _BCS:
        layer = bounded_context.removesuffix("_service")
        required_paths = (
            BASE / bounded_context / "bootstrap" / layer / "main.py",
            BASE / bounded_context / "bootstrap" / layer / "event_registry.py",
            BASE
            / bounded_context
            / "bootstrap"
            / layer
            / "container"
            / f"{layer}_core_container.py",
            BASE / bounded_context / "migrations" / "baseline.py",
            BASE / bounded_context / "docker" / "Dockerfile",
            BASE / bounded_context / "docker" / "docker-compose.yml",
        )
        missing.extend(
            f"{bounded_context}: {path.relative_to(BASE).as_posix()}"
            for path in required_paths
            if not path.is_file()
        )

        app_candidates = tuple(
            path
            for path in (BASE / bounded_context / "framework").rglob("app.py")
            if path.is_file()
        )
        if not app_candidates:
            missing.append(f"{bounded_context}: framework/**/api/app.py")

    assert not missing, "Incomplete standalone BC service surfaces:\n" + "\n".join(missing)


def test_service_surface_does_not_depend_on_legacy_monolith() -> None:
    legacy_root = BASE / "bootstrap" / "monolith"
    assert not legacy_root.exists(), f"Legacy monolith still exists: {legacy_root}"
