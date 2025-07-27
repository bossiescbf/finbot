from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.keyboards.inline import main_menu_keyboard

router = Router()

@router.message(Command("cancel"))
async def cancel_command(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            "❌ Нет активных действий для отмены.",
            reply_markup=main_menu_keyboard()
        )
        return

    await state.clear()
    await message.answer(
        "✅ Действие отменено. Возвращаемся в главное меню.",
        reply_markup=main_menu_keyboard()
    )

@router.callback_query(F.data.startswith("cancel"))
async def cancel_callback(callback: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "✅ Действие отменено. Возвращаемся в главное меню.",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer("Отменено")