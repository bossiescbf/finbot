from aiogram import Router, types
from aiogram.filters import Command
from app.database.crud import CategoryCRUD

router = Router()

@router.message(Command("categories"))
async def categories_command(message: types.Message, db):
    cats = await CategoryCRUD(db).list_for_user(message.from_user.id)
    text = "\n".join(f"{c.id}: {c.name}" for c in cats)
    await message.answer(f"Ваши категории:\n{text or 'Список пуст'}")