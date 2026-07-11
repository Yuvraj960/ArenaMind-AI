"""SQLAlchemy async session factory. DB connection failures on startup are non-fatal
in development — the app's simulator endpoints work without a database."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
import sys

from app.core.config import get_settings

settings = get_settings()

_engine = None
_async_session_maker = None


class Base(DeclarativeBase):
    pass


def _build_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            future=True,
            poolclass=NullPool,  # don't hold connections open before Postgres is up
        )
    return _engine


def get_engine():
    return _build_engine()


def async_session_maker() -> async_sessionmaker[AsyncSession]:
    global _async_session_maker
    if _async_session_maker is None:
        _async_session_maker = async_sessionmaker(
            _build_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_maker


async def get_db() -> AsyncSession:
    sm = async_session_maker()
    async with sm() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create tables. Pass silently if Postgres is unreachable."""
    try:
        engine = _build_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("[db] tables ready")
    except Exception as e:
        print(f"[db] init_db skipped (postgres not reachable): {e}")


async def close_db():
    if _engine:
        await _engine.dispose()