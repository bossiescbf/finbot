from aiogram import Router, types
from aiogram.filters import Command

router = Router()

@router.message(Command("settings"))
async def settings_command(message: types.Message) -> None:
    await message.answer("Настройки:\n1) Установить лимиты\n2) Сбросить данные")