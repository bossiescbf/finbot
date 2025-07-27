import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import async_session_factory
from app.database.crud import UserCRUD

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseMiddleware):
    """
    Middleware для аутентификации и инициализации пользователя.
    При каждом сообщении или callback:
    1) Открывает AsyncSession и кладёт в data['db']
    2) Получает или создаёт запись User в БД
    3) При создании нового пользователя добавляет категории по умолчанию
    4) Кладёт объект user в data['user']
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Обрабатываем только входящие сообщения и callback'и
        if isinstance(event, (Message, CallbackQuery)):
            # Открываем сессию к БД
            async with async_session_factory() as db:  # AsyncSession
                data["db"] = db

                # Извлекаем telegram_id
                tg_id = event.from_user.id

                # Получаем или создаём пользователя
                user, created = await UserCRUD.get_or_create_user(
                    db=db,
                    telegram_id=tg_id,
                    first_name=event.from_user.first_name or "",
                    username=event.from_user.username or ""
                )
                data["user"] = user

                if created:
                    logger.info(f"Создан новый пользователь {tg_id} и дефолтные категории")

                # Передаём управление дальше с db и user в data
                return await handler(event, data)

        # Для других типов апдейтов — просто пропускаем
        return await handler(event, data)