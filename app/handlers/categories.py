from aiogram import Router, types, F
from aiogram.filters import Command
from app.database.database import get_async_session
from app.database.crud import CategoryCRUD
from app.keyboards.inline import categories_management_keyboard

router = Router()

@router.message(Command("categories"))
async def categories_command(message: types.Message):
    async with get_async_session() as db:
        cats = await CategoryCRUD.get_user_categories(db, message.from_user.id)
        
        income_cats = [c for c in cats if c.is_income]
        expense_cats = [c for c in cats if not c.is_income]
        
        text = "📁 <b>Ваши категории:</b>\n\n"
        
        if income_cats:
            text += "💰 <b>Доходы:</b>\n"
            for c in income_cats:
                text += f"  {c.icon or '💰'} {c.name}\n"
            text += "\n"
        
        if expense_cats:
            text += "💸 <b>Расходы:</b>\n"
            for c in expense_cats:
                text += f"  {c.icon or '💸'} {c.name}\n"
        
        if not cats:
            text = "📁 Категории не найдены"
        
        await message.answer(text, parse_mode="HTML", reply_markup=categories_management_keyboard())

@router.callback_query(F.data == "categories")
async def categories_callback(callback: types.CallbackQuery):
    async with get_async_session() as db:
        cats = await CategoryCRUD.get_user_categories(db, callback.from_user.id)
        
        income_cats = [c for c in cats if c.is_income]
        expense_cats = [c for c in cats if not c.is_income]
        
        text = "📁 <b>Ваши категории:</b>\n\n"
        
        if income_cats:
            text += "💰 <b>Доходы:</b>\n"
            for c in income_cats:
                text += f"  {c.icon or '💰'} {c.name}\n"
            text += "\n"
        
        if expense_cats:
            text += "💸 <b>Расходы:</b>\n"
            for c in expense_cats:
                text += f"  {c.icon or '💸'} {c.name}\n"
        
        if not cats:
            text = "📁 Категории не найдены"
        
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=categories_management_keyboard())
        await callback.answer()