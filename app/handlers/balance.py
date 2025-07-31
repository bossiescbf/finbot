from aiogram import Router, types, F
from aiogram.filters import Command
from app.database.database import get_async_session
from app.database.crud import OperationCRUD
from app.keyboards.inline import balance_keyboard

router = Router()

@router.message(Command("balance"))
async def balance_command(message: types.Message):
    async with get_async_session() as db:
        balance_data = await OperationCRUD.get_balance(db, message.from_user.id)
        
        text = f"""
💰 <b>Ваш баланс:</b>

Общий баланс: <b>{balance_data['balance']} ₽</b>
Всего доходов: <b>{balance_data['total_income']} ₽</b>
Всего расходов: <b>{balance_data['total_expense']} ₽</b>
        """
        await message.answer(
            text.strip(),
            parse_mode="HTML",
            reply_markup=balance_keyboard()
        )

@router.callback_query(F.data == "balance")
async def balance_callback(callback: types.CallbackQuery):
    async with get_async_session() as db:
        balance_data = await OperationCRUD.get_balance(db, callback.from_user.id)
        
        text = f"""
💰 <b>Ваш баланс:</b>

Общий баланс: <b>{balance_data['balance']} ₽</b>
Всего доходов: <b>{balance_data['total_income']} ₽</b>
Всего расходов: <b>{balance_data['total_expense']} ₽</b>
        """
        await callback.message.edit_text(
            text.strip(),
            parse_mode="HTML",
            reply_markup=balance_keyboard()
        )
        await callback.answer()
        
@router.callback_query(F.data == "history")
async def history_callback(callback: types.CallbackQuery):
    """Показать последние 10 операций"""
    async with get_async_session() as db:
        ops = await OperationCRUD.get_recent_operations(db, callback.from_user.id, limit=10)

    if not ops:
        text = "🕑 История пустая."
    else:
        lines = []
        for op in ops:
            sign = "+" if op.is_income else "−"
            lines.append(f"{sign}{op.amount} ₽ — {op.category.name} ({op.created_at.strftime('%d.%m.%Y %H:%M')})")
        text = "🕑 <b>Последние 10 операций:</b>\n\n" + "\n".join(lines)

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=balance_keyboard()
    )
    await callback.answer()