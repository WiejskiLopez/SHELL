from __future__ import annotations

import importlib
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

service_package = context.config.get_main_option("service_package")
base_class = context.config.get_main_option("base_class")
if service_package is None or base_class is None:
    raise RuntimeError("alembic.ini must define service_package and base_class")
infra = importlib.import_module(service_package + ".infrastructure")
infra_root = Path(next(iter(infra.__path__)))
for model_path in infra_root.rglob("*.py"):
    if "models" not in model_path.parts or model_path.name == "__init__.py":
        continue
    relative = model_path.relative_to(infra_root).with_suffix("")
    module_name = ".".join(relative.parts)
    importlib.import_module(infra.__name__ + "." + module_name)
base_module = importlib.import_module(
    service_package + ".infrastructure.ingestion.persistence.sql.models.base"
)
target_metadata = getattr(base_module, base_class).metadata


def run_migrations_offline() -> None:
    context.configure(
        url=context.config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        context.config.get_section(context.config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    connectable.dispose()


run_migrations_offline() if context.is_offline_mode() else run_migrations_online()
