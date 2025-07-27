from aiogram import Router, types, F
from aiogram.filters import Command
from app.keyboards.inline import settings_menu_keyboard

router = Router()

@router.message(Command("settings"))
async def settings_command(message: types.Message):
    text = """
⚙️ <b>Настройки бота:</b>

Здесь вы можете настроить:
• Валюту для отображения
• Часовой пояс
• Лимиты трат
• Уведомления
• Экспорт/импорт данных
    """
    await message.answer(text.strip(), parse_mode="HTML", reply_markup=settings_menu_keyboard())

@router.callback_query(F.data == "settings")
async def settings_callback(callback: types.CallbackQuery):
    text = """
⚙️ <b>Настройки бота:</b>

Здесь вы можете настроить:
• Валюту для отображения
• Часовой пояс
• Лимиты трат
• Уведомления
• Экспорт/импорт данных
    """
    await callback.message.edit_text(text.strip(), parse_mode="HTML", reply_markup=settings_menu_keyboard())
    await callback.answer()