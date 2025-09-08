from sqlalchemy import Column, Table
from sqlalchemy.dialects.postgresql import TEXT, UUID

from .base import Base

metadata = Base.metadata

users = Table(
    "users",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("phone", TEXT),
    schema="auth",
)
