import os
import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv
from contextlib import asynccontextmanager

load_dotenv()

DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST     = os.getenv("DB_HOST")
DB_PORT     = os.getenv("DB_PORT")
DB_NAME     = os.getenv("DB_NAME")

required = {
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
    "DB_HOST": DB_HOST,
    "DB_PORT": DB_PORT,
    "DB_NAME": DB_NAME,
}
missing = [k for k, v in required.items() if not v]
if missing:
    raise RuntimeError(f"В .env отсутствуют переменные: {', '.join(missing)}")

DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=3600,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

@asynccontextmanager
async def get_async_session() -> AsyncSession:
    """
    Асинхронный контекстный менеджер для получения сессии SQLAlchemy.
    Использование:
        async with get_async_session() as db:
            ...
    """
    session: AsyncSession = async_session_maker()
    try:
        yield session
        await session.commit()
    except:
        await session.rollback()
        raise
    finally:
        await session.close()
        
async def init_database():
    """
    Инициализация базы данных (миграции, проверка схем).
    Вызывается при старте приложения.
    """
    # Здесь можно выполнить Alembic миграции или создание таблиц:
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    pass

async def close_database():
    """
    Закрытие движка и освобождение ресурсов.
    """
    await engine.dispose()