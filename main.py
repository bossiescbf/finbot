import os
import asyncio
import logging

from fastapi import FastAPI, Request, HTTPException, Header
from aiogram import Bot, Dispatcher
from aiogram.types import Update, Message
from aiogram.filters import Command
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest

# === Настройки бота и вебхука ===
API_TOKEN = "7803608584:AAGTvdUgfJ7sJMz91mWtS6zBYEQsK3MdDAw"
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = "https://brainrotanimal.store" + WEBHOOK_PATH
WEBHOOK_SECRET = "AAGTvdUgfJ7sJMz91mWtS6zBYEQsK3MdDAw"  # совпадает с секретом при set_webhook

# === Настройка логирования ===
LOG_DIR = "/var/log/finbot"
os.makedirs(LOG_DIR, exist_ok=True)  # убедитесь, что сервис имеет право на запись

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Получаем корневой логгер
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Handler для journal (stdout)
stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.INFO)
stdout_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
root_logger.addHandler(stdout_handler)

# FileHandler для INFO+ → app.log
app_file = logging.FileHandler(os.path.join(LOG_DIR, "app.log"))
app_file.setLevel(logging.INFO)
app_file.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
root_logger.addHandler(app_file)

# FileHandler для ERROR+ → error.log
err_file = logging.FileHandler(os.path.join(LOG_DIR, "error.log"))
err_file.setLevel(logging.ERROR)
err_file.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
root_logger.addHandler(err_file)

# === Инициализация бота и диспетчера ===
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    logging.info(f"Обрабатываю /start от пользователя {message.from_user.id}")
    await message.answer("Привет! Я твой финансовый бот.")

# === Настройка FastAPI ===
app = FastAPI(title="Финансовый Telegram Бот")

@app.get("/")
async def root():
    return {"message": "Финансовый бот работает", "status": "ok"}

@app.on_event("startup")
async def on_startup():
    try:
        info = await bot.get_webhook_info()
        current = info.url or ""
        if current != WEBHOOK_URL:
            await bot.delete_webhook(drop_pending_updates=True)
            for _ in range(3):
                try:
                    await bot.set_webhook(WEBHOOK_URL, secret_token=WEBHOOK_SECRET)
                    logging.info("Webhook установлен: %s", WEBHOOK_URL)
                    break
                except TelegramRetryAfter as e:
                    wait = getattr(e, "retry_after", 1)
                    logging.warning("Flood limit exceeded, retry after %s s", wait)
                    await asyncio.sleep(wait)
    except TelegramBadRequest as e:
        logging.error("Не удалось установить webhook: %s", e)

@app.post(WEBHOOK_PATH)
async def handle_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(None)
):
    if WEBHOOK_SECRET and x_telegram_bot_api_secret_token != WEBHOOK_SECRET:
        logging.warning("Запрос к webhook с некорректным секретом")
        raise HTTPException(status_code=403, detail="Forbidden")
    try:
        payload = await request.json()
        update_id = payload.get("update_id", "unknown")
        logging.info(f"Получен webhook: {update_id}")
        update = Update(**payload)
        await dp.feed_update(bot, update)
        return {"ok": True}
    except TelegramBadRequest as e:
        logging.error("TelegramBadRequest при обработке webhook: %s", e)
        return {"ok": False, "error": str(e)}
    except Exception as e:
        logging.exception("Неожиданная ошибка при webhook: %s", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.on_event("shutdown")
async def on_shutdown():
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    finally:
        await bot.session.close()
    # Закрываем файловые хэндлеры
    for handler in root_logger.handlers:
        handler.close()

@app.get("/health")
async def health_check():
    try:
        me = await bot.get_me()
        info = await bot.get_webhook_info()
        return {
            "status": "ok",
            "bot_username": me.username,
            "webhook_url": info.url,
            "webhook_pending_updates": info.pending_update_count
        }
    except Exception as e:
        logging.error("Health check failed: %s", e)
        return {"status": "error", "error": str(e)}