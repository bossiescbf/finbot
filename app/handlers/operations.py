from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from app.database.crud import OperationCRUD
from app.keyboards.inline import categories_keyboard, operations_keyboard, main_menu_keyboard
from app.keyboards.inline import main_menu_keyboard
from sqlalchemy.ext.asyncio import AsyncSession

router = Router()

class OperationStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_category = State()

@router.callback_query(F.data == "add_income")
async def cmd_add_income(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text(
        "Введите сумму дохода (например, 1234.56):",
        reply_markup=None
    )
    await state.set_state(OperationStates.waiting_for_amount)
    await state.update_data(operation_type="income")
    await cb.answer()

@router.callback_query(F.data == "add_expense")
async def cmd_add_expense(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text(
        "Введите сумму расхода (например, 1234.56):",
        reply_markup=None
    )
    await state.set_state(OperationStates.waiting_for_amount)
    await state.update_data(operation_type="expense")
    await cb.answer()

@router.message(
    StateFilter(OperationStates.waiting_for_amount),
    F.text.regexp(r"^\d+(\.\d{1,2})?$")
)
async def process_amount(message: Message, state: FSMContext):
    data = await state.get_data()
    op_type = data["operation_type"]
    amount = float(message.text)
    await state.update_data(amount=amount)

    categories = await OperationCRUD.get_categories(message.from_user.id, op_type)
    kb = categories_keyboard(categories, operation_type=op_type)
    await message.answer("Выберите категорию:", reply_markup=kb)
    await state.set_state(OperationStates.waiting_for_category)

@router.message(
    StateFilter(OperationStates.waiting_for_amount),
    ~F.text.regexp(r"^\d+(\.\d{1,2})?$")
)
async def invalid_amount(message: Message):
    await message.reply("Неверный формат суммы. Введите число, например: 100 или 99.50.")

@router.callback_query(StateFilter(OperationStates.waiting_for_category))
async def process_category(cb: CallbackQuery, state: FSMContext, db: AsyncSession):
    data = await state.get_data()
    op_type = data["operation_type"]
    amount = data["amount"]
    category_id = int(cb.data.split("_", 1)[1])

    await OperationCRUD.create_operation(
        db,
        user_id=cb.from_user.id,
        type=op_type,
        amount=amount,
        category_id=category_id
    )

    await state.clear()
    await cb.message.answer(
        f"✅ {'Доход' if op_type=='income' else 'Расход'} {amount:.2f} ₽ сохранён.",
        reply_markup=main_menu_keyboard()
    )
    await cb.answer()

# Optional: кнопка возврата в главное меню
@router.callback_query(F.data == "back_to_main")
async def back_to_main(cb: CallbackQuery):
    await cb.message.edit_text("Главное меню:", reply_markup=main_menu_keyboard())
    await cb.answer()