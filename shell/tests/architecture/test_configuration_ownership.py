"""Koncept: jawny ownership konfiguracji w composition roots.

Reguła: service bootstrap nie konsumuje monolitycznej konfiguracji bezposrednio
poza utworzeniem jawnych config slices.

Poprawnie: main.py uzywa deployment_config, platform_runtime_config,
service_config lub auth_config, a pola facade nie sa odczytywane bezposrednio.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_service_composition_roots_use_configuration_slices() -> None:
    main_files = tuple(ROOT.glob("*_service/bootstrap/*/main.py"))
    assert len(main_files) == 7

    forbidden = (
        "config.database_url",
        "config.events",
        "config.seed_dev_data",
        "config.api_key",
    )
    required_slices = (
        "config.deployment",
        "config.platform_runtime",
        "config.service",
    )

    for path in main_files:
        content = path.read_text(encoding="utf-8")
        assert not any(pattern in content for pattern in forbidden), path
        assert all(slice_name in content for slice_name in required_slices), path

    user_main = ROOT / "user_service" / "bootstrap" / "user" / "main.py"
    assert "config.auth" in user_main.read_text(encoding="utf-8")
