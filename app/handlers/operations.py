from aiogram import Router, types
from aiogram.filters import Command
from app.database.database import get_async_session
from app.database.crud import OperationCRUD

router = Router()

@router.message(Command("add"))
async def add_command(message: types.Message):
    # логика текстового ввода /add
    await message.reply("Введите сумму и описание операции…")

@router.callback_query(lambda c: c.data in ["add_income", "add_expense"])
async def add_callback(query: types.CallbackQuery):
    if query.data == "add_income":
        await query.message.answer("Ввод дохода: …")
    else:
        await query.message.answer("Ввод расхода: …")
    await query.answer()  # закрыть «часики»