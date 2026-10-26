"""Async SQLAlchemy lifecycle inspired by GraphOne; optional until storage is selected."""
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from xsentiment.config.settings import get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def build_engine(database_url: str | None = None) -> AsyncEngine:
    settings = get_settings()
    url = database_url or settings.database_url
    options: dict[str, int] = {}
    if url.startswith("postgresql"):
        options.update(pool_size=settings.db_pool_size, max_overflow=settings.db_max_overflow,
                       pool_timeout=settings.db_pool_timeout_seconds)
    return create_async_engine(url, **options)


def configure_database(database_url: str | None = None) -> AsyncEngine:
    global _engine, _session_factory
    if _engine is not None:
        raise RuntimeError("Database already configured; call close_database() first")
    _engine = build_engine(database_url)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)
    return _engine


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    if _session_factory is None:
        raise RuntimeError("Database is not configured; call configure_database() first")
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def close_database() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
