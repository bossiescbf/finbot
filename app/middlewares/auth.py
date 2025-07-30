from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud import UserCRUD
from app.database.models import User

class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Middleware для аутентификации пользователей"""
        
        # Получаем сессию базы данных
        db: AsyncSession = data.get('db')
        if not db:
            return await handler(event, data)
        
        # Извлекаем пользователя из события
        telegram_user = None
        if isinstance(event, (Message, CallbackQuery)):
            telegram_user = event.from_user
        elif hasattr(event, 'from_user'):
            telegram_user = event.from_user
        
        if not telegram_user:
            return await handler(event, data)
        
        try:
            # Получаем пользователя из БД или создаем нового
            user, is_new = await UserCRUD.get_or_create_user(
                db=db,
                telegram_id=telegram_user.id,
                first_name=telegram_user.first_name or "Пользователь",
                last_name=telegram_user.last_name,
                username=telegram_user.username
            )
            
            # Добавляем пользователя в данные обработчика
            data['user'] = user
            data['is_new_user'] = is_new
            
        except Exception as e:
            # Логируем ошибку, но не блокируем выполнение
            print(f"Ошибка в AuthMiddleware: {e}")
            data['user'] = None
            data['is_new_user'] = False
        
        return await handler(event, data)

def auth_required(handler):
    """Декоратор для обработчиков, требующих аутентификации"""
    async def wrapper(event, **kwargs):
        user = kwargs.get('user')
        if not user:
            if isinstance(event, Message):
                await event.reply("❌ Ошибка аутентификации. Используйте /start для регистрации.")
            elif isinstance(event, CallbackQuery):
                await event.answer("❌ Ошибка аутентификации. Используйте /start для регистрации.")
            return
        
        # Создаем динамический список параметров на основе сигнатуры функции
        import inspect
        sig = inspect.signature(handler)
        filtered_kwargs = {}
        
        for param_name in sig.parameters:
            if param_name != 'event' and param_name in kwargs:
                filtered_kwargs[param_name] = kwargs[param_name]
        
        return await handler(event, **filtered_kwargs)
    
    return wrapper