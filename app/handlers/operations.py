from aiogram import Router, types, F
from aiogram.filters import Command
from app.database.crud import OperationCRUD

router = Router()

# Команда /add
@router.message(Command("add"))
async def cmd_add(message: types.Message):
    await message.answer("Выберите тип операции:", reply_markup=operations_keyboard())

# Обработчик кнопок
@router.callback_query(F.data.in_(["add_income", "add_expense"]))
async def cb_add(callback: types.CallbackQuery, db):
    kind = "income" if callback.data == "add_income" else "expense"
    await callback.message.answer(f"Ввод {kind}…")
    await callback.answer()