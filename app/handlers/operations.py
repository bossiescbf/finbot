from aiogram import Router, types
from aiogram.filters import Command, Text
from app.database.crud import OperationCRUD

router = Router()

@router.message(Command("add"))
async def add_command(message: types.Message):
    await message.answer("Напишите операцию в формате:\n`+5000 зарплата` или `1200 обед`", parse_mode="Markdown")

@router.message(Text(startswith="+") | Text(regex=r"^\d"))
async def quick_add(message: types.Message, db):
    # Простейший парсер
    parts = message.text.split(maxsplit=1)
    amount = parts[0]
    description = parts[1] if len(parts) > 1 else ""
    kind = "income" if amount.startswith("+") else "expense"
    await OperationCRUD(db).create(
        user_id=message.from_user.id,
        amount=amount.strip("+"),
        kind=kind,
        description=description
    )
    await message.answer("Операция добавлена.")