from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import crud
from app.database.models import User

class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        db: AsyncSession = data.get('db')
        telegram_user = event.from_user
        
        # Получаем пользователя из БД
        user = await crud.get_user_by_telegram_id(db, telegram_user.id)
        
        if not user:
            # Создаем нового пользователя с базовыми категориями
            user = await crud.create_user(
                db=db,
                telegram_id=telegram_user.id,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                username=telegram_user.username
            )
        
        data['user'] = user
        return await handler(event, data)

def auth_required(handler):
    """Декоратор для обработчиков, требующих аутентификации"""
    async def wrapper(event, *args, **kwargs):
        user = kwargs.get('user')
        if not user:
            if isinstance(event, Message):
                await event.reply("❌ Пользователь не найден")
            elif isinstance(event, CallbackQuery):
                await event.answer("❌ Пользователь не найден")
            return
        
        return await handler(event, *args, **kwargs)
    
    return wrapper