from aiogram import Router, types
from aiogram.filters import Command
from app.database.crud import OperationCRUD

router = Router()

@router.message(Command("report"))
async def report_command(message: types.Message, db) -> None:
    ops = await OperationCRUD(db).list_for_user(message.from_user.id)
    text = "\n".join(f"{o.ts.date()}: {o.kind} {o.amount}" for o in ops)
    await message.answer(f"Отчёт:\n{text or 'Нет операций за период'}")