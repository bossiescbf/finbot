from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os

# 1. URL подключения к БД (пример для PostgreSQL + asyncpg)
DATABASE_URL = os.getenv(
    "SQLALCHEMY_DATABASE_URL",
    "postgresql+asyncpg://user:password@localhost:5432/your_db"
)

# 2. Создаём асинхронный движок
engine = create_async_engine(
    DATABASE_URL,
    echo=False,               # True для логирования SQL-запросов
    future=True
)

# 3. Фабрика сессий
async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,   # чтобы объекты не сбрасывались после commit
    class_=AsyncSession
)

# 4. Депенденси (для FastAPI) или контекстный менеджер (для middleware aiogram)
async def get_async_session() -> AsyncSession:
    """
    Используйте в FastAPI через Depends:
        async def endpoint(
            session: AsyncSession = Depends(get_async_session)
        ):
            ...
    Или в Aiogram middleware:
        async with async_session_factory() as session:
            data["db"] = session
    """
    async with async_session_factory() as session:
        yield session