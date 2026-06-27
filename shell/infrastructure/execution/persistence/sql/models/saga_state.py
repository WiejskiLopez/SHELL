from __future__ import annotations

from shell.infrastructure.platform.persistence.sql.models._compat import JSONB
from shell.infrastructure.platform.persistence.sql.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column, declared_attr
from shell.infrastructure.platform.persistence.sql.models.mixins import VersionedMixin


class GraphExecutionSagaStateModel(Base, VersionedMixin):
    __tablename__ = "saga_graph_execution_initialization"

    id: Mapped[str] = mapped_column(primary_key=True)
    graph_execution_id: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    expected_nodes_count: Mapped[int] = mapped_column(nullable=False)
    graph_node_definition_executions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(nullable=False, default="PENDING")

    @declared_attr
    def __mapper_args__(cls) -> dict:
        return {"version_id_col": cls.version}
