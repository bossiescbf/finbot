import asyncio
import logging
import os

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from dotenv import load_dotenv
from sqlalchemy import text

from app.database.database import init_database, close_database, engine
from app.handlers import (
    start_router, help_router, balance_router,
    operations_router, reports_router,
    categories_router, settings_router, cancel_router
)
from app.middlewares.auth import AuthMiddleware
from app.middlewares.logging import LoggingMiddleware

# 1. Загрузка .env
load_dotenv()

# 2. Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/var/log/finbot/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 3. Конфигурация
BOT_TOKEN    = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/telegram/webhook")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
DOMAIN       = os.getenv("DOMAIN")        # если задано — webhook, иначе polling
REDIS_URL    = os.getenv("REDIS_URL", "redis://localhost:6379/0")

if not BOT_TOKEN or not WEBHOOK_SECRET:
    raise ValueError("Необходимы BOT_TOKEN и WEBHOOK_SECRET")

# 4. Создаем бота и диспетчер
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
try:
    storage = RedisStorage.from_url(REDIS_URL)
    logger.info("Используется Redis для хранения FSM")
except Exception as e:
    storage = MemoryStorage()
    logger.warning(f"Redis недоступен ({e}), используется MemoryStorage")

dp = Dispatcher(storage=storage)

# 5. Регистрация middleware и роутеров
def setup_handlers():
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    dp.include_router(start_router)
    dp.include_router(help_router)
    dp.include_router(balance_router)
    dp.include_router(operations_router)
    dp.include_router(reports_router)
    dp.include_router(categories_router)
    dp.include_router(settings_router)
    dp.include_router(cancel_router)
    logger.info("Обработчики Telegram-бота зарегистрированы")

# 6. Хэндлеры старта и завершения AioHTTP-приложения
async def on_startup(app: web.Application):
    logger.info("on_startup: инициализация БД")
    await init_database()

    if DOMAIN:
        webhook_url = f"{DOMAIN}{WEBHOOK_PATH}"
        await bot.set_webhook(
            url=webhook_url,
            secret_token=WEBHOOK_SECRET,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True
        )
        logger.info(f"Webhook установлен: {webhook_url}")

    setup_handlers()

async def on_cleanup(app: web.Application):
    logger.info("on_cleanup: завершение приложения")
    await bot.delete_webhook(drop_pending_updates=True)
    await close_database()
    await storage.close()
    await bot.session.close()

# 7. Фабрика AioHTTP-приложения
def create_app() -> web.Application:
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    # Webhook
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET) \
        .register(app, path=WEBHOOK_PATH)

    # Health-check
    async def health(request):
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
                }
            })
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return web.json_response({"status": "unhealthy", "error": str(e)}, status=500)

    app.router.add_get("/health", health)
    app.router.add_get("/", lambda r: web.Response(text="FinBot is running!"))
    return app

# 8. Точка входа для запуска
aio_app = create_app()

async def main():
    if DOMAIN:
        logger.info("Запуск в режиме webhook")
        setup_application(aio_app, dp, bot=bot)
        runner = web.AppRunner(aio_app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 8000)
        await site.start()
        logger.info("AioHTTP сервер запущен на 127.0.0.1:8000")
        await asyncio.Event().wait()
    else:
        logger.info("Запуск в режиме polling")
        await bot.delete_webhook(drop_pending_updates=True)
        await init_database()
        try:
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types(), drop_pending_updates=True)
        finally:
            await close_database()
            await storage.close()
            await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Получен SIGINT, завершаем")
    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
        raise