from aiogram import Router, types, F
from aiogram.filters import Command
from app.database.database import get_async_session
from app.database.crud import OperationCRUD
from app.keyboards.inline import reports_menu_keyboard

router = Router()

@router.message(Command("report"))
async def report_command(message: types.Message):
    async with get_async_session() as db:
        ops = await OperationCRUD.get_user_operations(db, message.from_user.id, limit=20)
        
        if not ops:
            await message.answer("📊 Нет операций за период", reply_markup=reports_menu_keyboard())
            return
            
        text = "📊 <b>Последние операции:</b>\n\n"
        for o in ops:
            emoji = "💰" if o.type == "income" else "💸"
            date_str = o.occurred_at.strftime('%d.%m.%Y %H:%M')
            text += f"{emoji} <b>{date_str}</b> - {o.amount} ₽\n"
            text += f"   📁 {o.category_name}\n"
            if o.description:
                text += f"   💬 {o.description}\n"
            text += "\n"
        
        await message.answer(text, parse_mode="HTML", reply_markup=reports_menu_keyboard())

@router.callback_query(F.data == "reports")
async def reports_callback(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📊 <b>Выберите тип отчета:</b>",
        parse_mode="HTML",
        reply_markup=reports_menu_keyboard()
    )
    await callback.answer()