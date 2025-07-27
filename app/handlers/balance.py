from aiogram import Router, types
from aiogram.filters import Command
from app.database.crud import UserCRUD

router = Router()

@router.message(Command("balance"))
async def balance_command(message: types.Message, db):
    balance = await UserCRUD(db).get_balance(message.from_user.id)
    await message.answer(f"Ваш текущий баланс: {balance}")