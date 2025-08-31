"""
Joyce Database Module

Async-ready database foundations with PostgreSQL for persistent storage
of memories, user profiles, and metadata. Vector storage and search
capabilities are provided by the separate `joyce.vs` module.
"""

from __future__ import annotations

from .client import (
    SessionMaker,
    create_async_engine_from_env,
    create_session_maker,
    engine,
    get_db_session,
    init_database,
)

__all__ = [
    "SessionMaker",
    "create_async_engine_from_env",
    "create_session_maker",
    "engine",
    "get_db_session",
    "init_database",
]
