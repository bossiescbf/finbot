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

# app/middlewares/logging.py
import logging
from typing import Callable, Dict, Any, Awaitable
from datetime import datetime
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseMiddleware):
    """Middleware для логирования действий пользователей"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Получаем информацию о пользователе
        user_info = "Unknown"
        action_info = "Unknown action"
        
        if isinstance(event, Message):
            user = event.from_user
            user_info = f"@{user.username or user.id} ({user.first_name})"
            
            if event.text:
                action_info = f"Message: {event.text[:50]}{'...' if len(event.text) > 50 else ''}"
            elif event.content_type:
                action_info = f"Content: {event.content_type}"
                
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            user_info = f"@{user.username or user.id} ({user.first_name})"
            action_info = f"Callback: {event.data}"
        
        # Логируем начало обработки
        start_time = datetime.now()
        logger.info(f"[{start_time.strftime('%H:%M:%S')}] {user_info} -> {action_info}")
        
        try:
            # Вызываем обработчик
            result = await handler(event, data)
            
            # Логируем успешное завершение
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"[{end_time.strftime('%H:%M:%S')}] ✅ Processed in {duration:.2f}s")
            
            return result
            
        except Exception as e:
            # Логируем ошибку
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.error(f"[{end_time.strftime('%H:%M:%S')}] ❌ Error after {duration:.2f}s: {e}")
            
            # Отправляем пользователю сообщение об ошибке
            if isinstance(event, Message):
                try:
                    await event.answer(
                        "❌ Произошла ошибка при обработке запроса. Попробуй еще раз или обратись к администратору."
                    )
                except:
                    pass
            elif isinstance(event, CallbackQuery):
                try:
                    await event.answer("Произошла ошибка. Попробуй еще раз.", show_alert=True)
                except:
                    pass
            
            # Переподнимаем исключение
            raise