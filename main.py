import asyncio, logging, os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from dotenv import load_dotenv

from app.database.database import init_database, close_database, engine
from app.handlers import start
from app.middlewares.auth import AuthMiddleware
from app.middlewares.logging import LoggingMiddleware

load_dotenv()

# Логи
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/var/log/finbot/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/telegram/webhook")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
DOMAIN = os.getenv("DOMAIN")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

if not BOT_TOKEN or not WEBHOOK_SECRET:
    raise ValueError("Необходимы BOT_TOKEN и WEBHOOK_SECRET")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

try:
    storage = RedisStorage.from_url(REDIS_URL)
    logger.info("Redis FSM storage")
except:
    storage = MemoryStorage()
    logger.warning("Memory FSM storage")

dp = Dispatcher(storage=storage)

# Startup/shutdown handlers
async def on_startup(app: web.Application):
    logger.info("Startup: init database")
    await init_database()
    if DOMAIN:
        url = f"{DOMAIN}{WEBHOOK_PATH}"
        await bot.set_webhook(url=url, secret_token=WEBHOOK_SECRET,
                               allowed_updates=dp.resolve_used_update_types(),
                               drop_pending_updates=True)
        logger.info(f"Webhook set: {url}")
    setup_handlers()

async def on_cleanup(app: web.Application):
    logger.info("Cleanup: delete webhook and close resources")
    await bot.delete_webhook(drop_pending_updates=True)
    await close_database()
    await storage.close()
    await bot.session.close()

def setup_handlers():
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    dp.include_router(start.router)
    logger.info("Handlers registered")

def create_app() -> web.Application:
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    # Webhook handler
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET) \
        .register(app, path=WEBHOOK_PATH)

    # Health
    async def health(request):
        try:
            me = await bot.get_me()
            async with engine.begin() as conn:
                await conn.execute("SELECT 1")
            return web.json_response({"status":"healthy","bot":me.dict()})
        except Exception as e:
            return web.json_response({"status":"unhealthy","error":str(e)}, status=500)

    app.router.add_get("/health", health)
    app.router.add_get("/", lambda r: web.Response(text="FinBot is running!"))
    return app

async def main():
    if DOMAIN:
        logger.info("Webhook mode")
        setup_application(app, dp, bot=bot)
        runner = web.AppRunner(app); await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 8000); await site.start()
        await asyncio.Event().wait()
    else:
        logger.info("Polling mode")
        await bot.delete_webhook(drop_pending_updates=True)
        await init_database()
        try:
            await dp.start_polling(bot, drop_pending_updates=True)
        finally:
            await close_database()
            await storage.close()
            await bot.session.close()

def make_app():
    """
    Фабрика для systemd-юнита uvicorn.service,
    который будет вызывать main:make_app как ASGI-функцию.
    """
    return create_app()

# ASGI-приложение для uvicorn: main:app (alias на make_app)
app = make_app

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown by user")
    except Exception:
        logger.exception("Critical error")