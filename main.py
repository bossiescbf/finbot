import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from sqlalchemy import text

from config import settings
from app.database.database import init_database, close_database, engine
from app.handlers.start import router as start_router
from app.handlers.help import router as help_router
from app.handlers.balance import router as balance_router
from app.handlers.operations import router as operations_router
from app.handlers.reports import router as reports_router
from app.handlers.categories import router as categories_router
from app.handlers.settings import router as settings_router
from app.handlers.cancel import router as cancel_router

from app.middlewares.auth import AuthMiddleware
from app.middlewares.logging import LoggingMiddleware

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/var/log/finbot/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Создание бота
bot = Bot(
    token=settings.bot.token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Настройка хранилища FSM
try:
    storage = RedisStorage.from_url(settings.redis_url)
    logger.info("Используется Redis для хранения FSM")
except Exception as e:
    storage = MemoryStorage()
    logger.warning(f"Redis недоступен ({e}), используется MemoryStorage")

# Создание диспетчера
dp = Dispatcher(storage=storage)

def setup_handlers():
    """Регистрация middleware и роутеров"""
    # Middleware
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    
    # Роутеры
    dp.include_router(start_router)
    dp.include_router(help_router)
    dp.include_router(balance_router)
    dp.include_router(operations_router)
    dp.include_router(reports_router)
    dp.include_router(categories_router)
    dp.include_router(settings_router)
    dp.include_router(cancel_router)
    
    logger.info("Обработчики Telegram-бота зарегистрированы")

# События жизненного цикла приложения
async def on_startup(app: web.Application):
    """Инициализация при запуске"""
    logger.info("Инициализация базы данных")
    await init_database()
    
    if settings.use_webhook:
        webhook_url = f"{settings.domain}{settings.webhook_path}"
        await bot.set_webhook(
            url=webhook_url,
            secret_token=settings.webhook_secret,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True
        )
        logger.info(f"Webhook установлен: {webhook_url}")

async def on_cleanup(app: web.Application):
    """Очистка при завершении"""
    logger.info("Завершение работы приложения")
    await bot.delete_webhook(drop_pending_updates=True)
    await close_database()
    await storage.close()
    await bot.session.close()

def create_app() -> web.Application:
    """Создание AioHTTP приложения"""
    app = web.Application()
    
    # События жизненного цикла
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    
    # Webhook обработчик
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.webhook_secret
    ).register(app, path=settings.webhook_path)
    
    # Health check эндпоинт
    async def health_check(request):
        """Проверка состояния сервиса"""
        try:
            me = await bot.get_me()
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            return web.json_response({
                "status": "healthy",
                "bot": {
                    "id": me.id,
                    "username": me.username,
                    "first_name": me.first_name
                },
                "database": "connected"
            })
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return web.json_response(
                {"status": "unhealthy", "error": str(e)}, 
                status=500
            )
    
    # Роутинг
    app.router.add_get("/health", health_check)
    app.router.add_get("/", lambda r: web.Response(text="FinBot is running!"))
    
    return app

async def run_webhook():
    """Запуск в режиме webhook"""
    logger.info("Запуск в режиме webhook")
    
    app = create_app()
    setup_application(app, dp, bot=bot)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, "127.0.0.1", 8000)
    await site.start()
    
    logger.info(f"Webhook сервер запущен на 127.0.0.1:8000")
    logger.info(f"Webhook URL: {settings.domain}{settings.webhook_path}")
    
    # Держим сервер запущенным
    await asyncio.Event().wait()

async def run_polling():
    """Запуск в режиме polling"""
    logger.info("Запуск в режиме polling")
    
    await bot.delete_webhook(drop_pending_updates=True)
    await init_database()
    
    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True
        )
    finally:
        await close_database()
        await storage.close()
        await bot.session.close()

async def main():
    """Основная функция запуска"""
    # Регистрация обработчиков
    setup_handlers()
    
    # Выбор режима запуска
    if settings.use_webhook:
        await run_webhook()
    else:
        await run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Получен сигнал завершения (SIGINT)")
    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
        raise