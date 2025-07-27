from aiogram import Router, types, F
from aiogram.filters import Command
from app.database.database import get_async_session
from app.database.crud import OperationCRUD

router = Router()

@router.message(Command("balance"))
async def balance_command(message: types.Message):
    async with get_async_session() as db:
        balance_data = await OperationCRUD.get_balance(db, message.from_user.id)
        
        text = f"""
💰 <b>Ваш баланс:</b>

┣ Общий баланс: <b>{balance_data['balance']} ₽</b>
┣ Всего доходов: <b>{balance_data['total_income']} ₽</b>
┗ Всего расходов: <b>{balance_data['total_expense']} ₽</b>
        """
        await message.answer(text.strip(), parse_mode="HTML")

@router.callback_query(F.data == "balance")
async def balance_callback(callback: types.CallbackQuery):
    async with get_async_session() as db:
        balance_data = await OperationCRUD.get_balance(db, callback.from_user.id)
        
        text = f"""
💰 <b>Ваш баланс:</b>

┣ Общий баланс: <b>{balance_data['balance']} ₽</b>
┣ Всего доходов: <b>{balance_data['total_income']} ₽</b>
┗ Всего расходов: <b>{balance_data['total_expense']} ₽</b>
        """
        await callback.message.edit_text(text.strip(), parse_mode="HTML")
        await callback.answer()