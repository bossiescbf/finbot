from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.database import get_async_session
from ..database.crud import UserCRUD
from ..keyboards.inline import main_menu_keyboard
from ..schemas.user import UserCreate

router = Router()

@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    # Очищаем состояние если есть
    await state.clear()
    
    # Получаем сессию БД
    async with get_async_session() as db:
        # Получаем или создаем пользователя
        user, is_new = await UserCRUD.get_or_create_user(
            db,
            telegram_id=message.from_user.id,
            first_name=message.from_user.first_name or "Неизвестно",
            last_name=message.from_user.last_name,
            username=message.from_user.username
        )
    
    if is_new:
        welcome_text = f"""
🎉 <b>Добро пожаловать в FinBot!</b>

Привет, {message.from_user.first_name}! Я твой личный финансовый помощник.

<b>Что я умею:</b>
💰 Учитывать доходы и расходы
📊 Строить отчеты и статистику  
📈 Показывать баланс
📁 Управлять категориями
⚙️ Настраивать бюджеты и лимиты

<b>Для быстрого добавления операций</b> просто напиши:
• <code>1200 обед</code> - добавить расход
• <code>+5000 зарплата</code> - добавить доход

Я уже создал для тебя базовые категории. Начнем! 👇
        """
    else:
        welcome_text = f"""
👋 <b>С возвращением, {message.from_user.first_name}!</b>

Рад тебя видеть снова! Выбери, что хочешь сделать:
        """
    
    await message.answer(
        welcome_text.strip(),
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    
    text = f"""
🏠 <b>Главное меню</b>

Выбери нужное действие:
    """
    
    await callback.message.edit_text(
        text.strip(),
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(Command("menu"))
async def menu_command(message: Message, state: FSMContext):
    """Показать главное меню"""
    await state.clear()
    
    text = f"""
🏠 <b>Главное меню</b>

Выбери нужное действие, {message.from_user.first_name}:
    """
    
    await message.answer(
        text.strip(),
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )

@router.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext):
    """Отмена текущего действия"""
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer(
            "❌ Нет активных действий для отмены.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    await state.clear()
    await message.answer(
        "✅ Действие отменено. Возвращаемся в главное меню.",
        reply_markup=main_menu_keyboard()
    )

@router.callback_query(F.data.startswith("cancel"))
async def cancel_callback(callback: CallbackQuery, state: FSMContext):
    """Отмена через callback"""
    await state.clear()
    
    await callback.message.edit_text(
        "✅ Действие отменено. Возвращаемся в главное меню.",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer("Отменено")

@router.message(Command("status"))
async def status_command(message: Message):
    """Показать статус бота и пользователя"""
    async with get_async_session() as db:
        user = await UserCRUD.get_by_telegram_id(db, message.from_user.id)
        
        if not user:
            await message.answer("❌ Пользователь не найден. Используй /start для регистрации.")
            return
        
        status_text = f"""
📊 <b>Статус аккаунта</b>

<b>👤 Пользователь:</b> {user.first_name} {user.last_name or ''}
<b>🆔 ID:</b> <code>{user.telegram_id}</code>
<b>💱 Валюта:</b> {user.currency}
<b>🌍 Часовой пояс:</b> {user.timezone}
<b>📅 Регистрация:</b> {user.created_at.strftime('%d.%m.%Y %H:%M')}

<b>🔔 Уведомления:</b> {'✅ Включены' if user.notification_enabled else '❌ Отключены'}
<b>📊 Дневной лимит:</b> {f'{user.daily_limit:,.0f} {user.currency}'.replace(',', ' ') if user.daily_limit else 'Не установлен'}
<b>📈 Месячный лимит:</b> {f'{user.monthly_limit:,.0f} {user.currency}'.replace(',', ' ') if user.monthly_limit else 'Не установлен'}

<b>📱 Бот:</b> Работает нормально ✅
<b>🗄️ База данных:</b> Подключена ✅
        """
        
        await message.answer(
            status_text.strip(),
            parse_mode="HTML",
            reply_markup=main_menu_keyboard()
        )

# Обработчик неизвестных команд
@router.message(F.text.startswith("/"))
async def unknown_command(message: Message):
    command = message.text.split()[0]
    await message.answer(
        f"❓ Неизвестная команда: <code>{command}</code>\n\n"
        "Используй /help для просмотра всех доступных команд.",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )