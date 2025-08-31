"""
Shared SQLAlchemy declarative base for Joyce database models.

All database models should inherit from the Base class defined here
to ensure consistent table metadata and model registration.
"""

from __future__ import annotations

from sqlalchemy.orm import declarative_base

Base = declarative_base()
