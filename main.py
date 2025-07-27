import asyncio
import logging
import os
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Импорты приложения
from app.database.database import init_database, close_database
from app.handlers import start
# from app.handlers import operations, categories, reports, settings
from app.middlewares.auth import AuthMiddleware
from app.middlewares.logging import LoggingMiddleware

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/finbot/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/telegram/webhook")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
DOMAIN = os.getenv("DOMAIN")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Проверка обязательных переменных
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен в переменных окружения")

if not WEBHOOK_SECRET:
    raise ValueError("WEBHOOK_SECRET не установлен в переменных окружения")

# Создание бота и диспетчера
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

# Выбор хранилища состояний
try:
    # Пытаемся использовать Redis для хранения состояний
    storage = RedisStorage.from_url(REDIS_URL)
    logger.info("Используется Redis для хранения состояний FSM")
except Exception as e:
    logger.warning(f"Не удалось подключиться к Redis: {e}. Используется память.")
    storage = MemoryStorage()

dp = Dispatcher(storage=storage)

@asynccontextmanager
async def lifespan(app: web.Application):
    """Управление жизненным циклом приложения"""
    # Запуск
    logger.info("Запуск приложения...")
    
    # Инициализация базы данных
    await init_database()
    logger.info("База данных инициализирована")
    
    # Установка webhook
    if DOMAIN:
        webhook_url = f"{DOMAIN}{WEBHOOK_PATH}"
        await bot.set_webhook(
            url=webhook_url,
            secret_token=WEBHOOK_SECRET,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True
        )
        logger.info(f"Webhook установлен: {webhook_url}")
    
    yield
    
    # Завершение
    logger.info("Завершение приложения...")
    
    # Удаление webhook
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook удален")
    
    # Закрытие подключений
    await close_database()
    await storage.close()
    await bot.session.close()
    
    logger.info("Приложение завершено")

def setup_handlers():
    """Регистрация обработчиков"""
    # Подключение middleware
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    
    # Подключение роутеров
    dp.include_router(start.router)
    
    # TODO: Подключить остальные роутеры
    # dp.include_router(operations.router)
    # dp.include_router(categories.router)
    # dp.include_router(reports.router)
    # dp.include_router(settings.router)
    
    logger.info("Обработчики зарегистрированы")

def create_app() -> web.Application:
    """Создание FastAPI приложения"""
    app = web.Application()
    
    # Настройка webhook handler
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    # Health check endpoint
    async def health_check(request):
        """Проверка здоровья приложения"""
        try:
            # Проверка бота
            bot_info = await bot.get_me()
            
            # Проверка базы данных
            from app.database.database import engine
            async with engine.begin() as conn:
                await conn.execute("SELECT 1")
            
            return web.json_response({
                "status": "healthy",
                "bot": {
                    "id": bot_info.id,
                    "username": bot_info.username,
                    "first_name": bot_info.first_name
                },
                "database": "connected",
                "timestamp": asyncio.get_event_loop().time()
            })
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return web.json_response({
                "status": "unhealthy",
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }, status=500)
    
    # Добавление маршрутов
    app.router.add_get("/health", health_check)
    app.router.add_get("/", lambda request: web.Response(text="FinBot is running!"))
    
    return app

async def main():
    """Основная функция запуска"""
    try:
        # Настройка обработчиков
        setup_handlers()
        
        # Создание веб-приложения
        app = create_app()
        
        if DOMAIN:
            # Режим webhook (production)
            logger.info("Запуск в режиме webhook")
            
            # Настройка приложения для webhook
            setup_application(app, dp, bot=bot)
            
            # Запуск веб-сервера
            runner = web.AppRunner(app)
            await runner.setup()
            
            site = web.TCPSite(runner, host="127.0.0.1", port=8000)
            await site.start()
            
            logger.info("Сервер запущен на http://127.0.0.1:8000")
            
            # Ожидание завершения
            await asyncio.Event().wait()
            
        else:
            # Режим polling (development)
            logger.info("Запуск в режиме polling")
            
            # Удаляем webhook если установлен
            await bot.delete_webhook(drop_pending_updates=True)
            
            # Инициализация базы данных
            await init_database()
            
            try:
                # Запуск polling
                await dp.start_polling(
                    bot,
                    allowed_updates=dp.resolve_used_update_types(),
                    drop_pending_updates=True
                )
            finally:
                await close_database()
                await storage.close()
                
    except Exception as e:
        logger.error(f"Ошибка запуска: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise