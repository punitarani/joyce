"""
Database client module for Joyce.

Provides async database engine, session management, and connection utilities
for PostgreSQL operations using SQLAlchemy async features.
"""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from joyce.env import env


def create_async_engine_from_env(**kwargs) -> AsyncEngine:
    """
    Create async SQLAlchemy engine from environment configuration.

    Args:
        **kwargs: Additional arguments passed to create_async_engine()

    Returns:
        AsyncEngine: Configured async database engine
    """
    return create_async_engine(env.DB_URL, **kwargs)


def create_session_maker(
    engine: AsyncEngine, **kwargs
) -> async_sessionmaker[AsyncSession]:
    """
    Create async session maker for database operations.

    Args:
        engine: Async database engine
        **kwargs: Additional arguments passed to async_sessionmaker()

    Returns:
        async_sessionmaker: Session factory for creating database sessions
    """
    return async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession, **kwargs
    )


async def init_database(engine: AsyncEngine, base) -> None:
    """
    Initialize database tables using SQLAlchemy metadata.

    Args:
        engine: Async database engine
        base: SQLAlchemy declarative base containing table metadata
    """
    async with engine.begin() as conn:
        await conn.run_sync(base.metadata.create_all)


async def get_session(
    session_maker: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session from session maker.

    Args:
        session_maker: Session factory for creating database sessions

    Yields:
        AsyncSession: Database session for operations
    """
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


# Global instances (initialized on import)
engine = create_async_engine_from_env(echo=env.is_development)
SessionMaker = create_session_maker(engine)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection helper for database sessions.

    Creates and yields a database session using the global SessionMaker.
    Commonly used with FastAPI dependency injection.

    Yields:
        AsyncSession: Database session for operations
    """
    async with SessionMaker() as session:
        try:
            yield session
        finally:
            await session.close()
