import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

load_dotenv()

# Подключение к базе данных
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://finbot_user:45171309@localhost:5432/finbot_db"
)

# Создание асинхронного движка
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Изменить на True для отладки SQL запросов
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Создание фабрики сессий
async_session_maker = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

Base = declarative_base()

async def get_async_session() -> AsyncSession:
    """Получение асинхронной сессии для работы с БД"""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_database():
    """Инициализация базы данных"""
    async with engine.begin() as conn:
        pass

async def close_database():
    """Закрытие подключения к БД"""
    await engine.dispose()