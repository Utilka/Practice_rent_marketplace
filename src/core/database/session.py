from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.config import get_settings

settings = get_settings()

async_engine = create_async_engine(
    settings.sqlalchemy_database_uri,
    echo=settings.debug,
)
session_factory = async_sessionmaker(
    async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session() -> AsyncSession:
    async with session_factory() as session:
        yield session
