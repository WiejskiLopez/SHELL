from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB as _PgJSONB

JSONB = JSON().with_variant(_PgJSONB(), "postgresql")
