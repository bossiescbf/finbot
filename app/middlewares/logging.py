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
         finally:
            # Всегда пропускаем событие дальше, даже если было исключение в логике логирования
            return await handler(event, data)