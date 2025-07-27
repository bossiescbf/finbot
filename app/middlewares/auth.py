from aiogram import types
from loguru import logger
from app.database.database import get_async_session

class AuthMiddleware:
    async def __call__(self, handler, event: types.Update, data: dict):
        """
        Middleware для проверки аутентификации и передачи сессии БД.
        event — объект aiogram.types.Update
        data  — словарь с контекстом до обработчика
        """
        # Получаем асинхронную сессию БД
        async with get_async_session() as db:
            data["db"] = db

            try:
                # Вызываем следующий обработчик
                return await handler(event, data)
            except Exception as e:
                logger.error(f"AuthMiddleware error: {e}")
                # Если пришло сообщение (не CallbackQuery), отвечаем в чат
                if event.message:
                    await event.message.reply(
                        "❌ Произошла ошибка при обработке запроса. Попробуйте ещё раз или обратитесь к администратору."
                    )
                return  # прерываем цепочку