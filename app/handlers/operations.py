from aiogram import Router, types, F
from aiogram.filters import Command
from app.database.database import get_async_session
from app.database.crud import OperationCRUD
from app.keyboards.inline import operations_keyboard

router = Router()

@router.message(Command("add"))
async def cmd_add(message: types.Message):
    await message.answer("💰 Выберите тип операции:", reply_markup=operations_keyboard())

@router.callback_query(F.data.in_(["add_income", "add_expense"]))
async def cb_add(callback: types.CallbackQuery):
    operation_type = "income" if callback.data == "add_income" else "expense"
    emoji = "💰" if operation_type == "income" else "💸"
    type_text = "доход" if operation_type == "income" else "расход"
    
    await callback.message.edit_text(
        f"{emoji} <b>Добавление операции: {type_text}</b>\n\n"
        f"Введите сумму и описание в формате:\n"
        f"<code>1000 описание</code>\n\n"
        f"Или просто сумму:\n"
        f"<code>1000</code>",
        parse_mode="HTML"
    )
    await callback.answer()