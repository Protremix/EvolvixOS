import uuid
from sqlalchemy import String, JSON
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.types import TypeDecorator

class GUID(TypeDecorator):
    """Platform-independent GUID type."""
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PGUUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value


class JSONType(TypeDecorator):
    """Platform-independent JSON type."""
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB)
        return dialect.type_descriptor(JSON)
