from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.database import get_async_session
from ..database.crud import UserCRUD

class AuthMiddleware(BaseMiddleware):
    """Middleware для аутентификации пользователей"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Получаем пользователя из события
        user = None
        if isinstance(event, (Message, CallbackQuery)):
            user = event.from_user
        
        if not user:
            # Если нет пользователя, пропускаем middleware
            return await handler(event, data)
        
        # Получаем сессию БД
        async for db in get_async_session():
            try:
                # Ищем пользователя в базе
                db_user = await UserCRUD.get_by_telegram_id(db, user.id)
                
                # Добавляем информацию о пользователе в данные
                data["db_user"] = db_user
                data["is_registered"] = db_user is not None
                data["db"] = db
                
                # Если пользователь не зарегистрирован, но это не команда /start
                if not db_user and not (isinstance(event, Message) and event.text and event.text.startswith('/start')):
                    if isinstance(event, Message):
                        await event.answer(
                            "❌ Ты не зарегистрирован. Используй команду /start для начала работы."
                        )
                    elif isinstance(event, CallbackQuery):
                        await event.answer("Используй команду /start для начала работы.", show_alert=True)
                    return
                
                # Вызываем обработчик
                return await handler(event, data)
                
            except Exception as e:
                # Логируем ошибку и продолжаем без БД
                print(f"Auth middleware error: {e}")
                return await handler(event, data)
            finally:
                await db.close()