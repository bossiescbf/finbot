from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.keyboards import inline

router = Router()

@router.message(Command("cancel"))
async def cancel_command(message: types.Message, state: FSMContext) -> None:
    """Отмена текущего действия"""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            "❌ Нет активных действий для отмены.",
            reply_markup=inline()
        )
        return

    await state.clear()
    await message.answer(
        "✅ Действие отменено. Возвращаемся в главное меню.",
        reply_markup=inline()
    )

@router.callback_query(F.data.startswith("cancel"))
async def cancel_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Отмена через callback"""
    await state.clear()
    await callback.message.edit_text(
        "✅ Действие отменено. Возвращаемся в главное меню.",
        reply_markup=inline()
    )
    await callback.answer("Отменено")