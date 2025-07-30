from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.crud import UserCRUD, OperationCRUD, CategoryCRUD
from app.keyboards.inline import get_category_selection_keyboard, main_menu_keyboard

router = Router()

class OperationStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_category = State()

@router.callback_query(F.data == "add_income")
async def cmd_add_income(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("Введите сумму дохода:", reply_markup=None)
    await state.set_state(OperationStates.waiting_for_amount)
    await state.update_data(operation_type="income")
    await cb.answer()

@router.callback_query(F.data == "add_expense")
async def cmd_add_expense(cb: CallbackQuery, state: FSMContext):
    await cb.message.edit_text("Введите сумму расхода:", reply_markup=None)
    await state.set_state(OperationStates.waiting_for_amount)
    await state.update_data(operation_type="expense")
    await cb.answer()

@router.message(
    StateFilter(OperationStates.waiting_for_amount),
    F.text.regexp(r"^\d+(\.\d{1,2})?$")
)
async def process_amount(message: Message, state: FSMContext, db: AsyncSession):
    data = await state.get_data()
    op_type = data["operation_type"]
    amount = float(message.text)
    await state.update_data(amount=amount)

    # Получаем пользователя
    user = await UserCRUD.get_by_telegram_id(db, message.from_user.id)
    if not user:
        await message.answer("❌ Пользователь не найден. Используйте /start для регистрации.")
        return

    # Получаем категории пользователя
    is_income = True if op_type == "income" else False
    categories = await CategoryCRUD.get_user_categories(
        db=db,
        user_id=user.id,
        is_income=is_income
    )
    
    if not categories:
        await message.answer("❌ У вас нет категорий для этого типа операций. Используйте /start для инициализации.")
        return
    
    # Используем функцию клавиатуры
    kb = get_category_selection_keyboard(categories, operation_type=op_type)
    await message.answer("Выберите категорию:", reply_markup=kb.as_markup())
    await state.set_state(OperationStates.waiting_for_category)

@router.message(
    StateFilter(OperationStates.waiting_for_amount),
    ~F.text.regexp(r"^\d+(\.\d{1,2})?$")
)
async def invalid_amount(message: Message):
    await message.reply("Неверный формат суммы. Введите число, например: 100 или 99.50.")

@router.callback_query(
    StateFilter(OperationStates.waiting_for_category),
    F.data.startswith("select_category:")
)
async def process_category(cb: CallbackQuery, state: FSMContext, db: AsyncSession):
    data = await state.get_data()
    op_type = data["operation_type"]
    amount = data["amount"]
    
    callback_parts = cb.data.split(":")
    category_id = int(callback_parts[1])

    # Получение пользователя из БД
    user = await UserCRUD.get_by_telegram_id(db, cb.from_user.id)
    if not user:
        await cb.answer("❌ Пользователь не найден")
        return

    # Создаем операцию
    from app.schemas.operation import OperationCreate
    from datetime import datetime, timezone
    
    op_create = OperationCreate(
        amount=amount,
        type=op_type,
        occurred_at=datetime.now(timezone.utc),
        category_id=category_id
    )

    try:
        await OperationCRUD.create(
            db=db,
            operation_data=op_create,
            user_id=user.id
        )

        # Получаем информацию о категории для отображения
        category = await CategoryCRUD.get_category_by_id(db, category_id)
        category_name = f"{category.icon} {category.name}" if category else "Неизвестная категория"

        await state.clear()
        await cb.message.edit_text(
            f"✅ {'Доход' if op_type=='income' else 'Расход'} {amount:.2f}₽ сохранён.\n"
            f"📁 Категория: {category_name}",
            reply_markup=main_menu_keyboard()
        )
        await cb.answer()

    except Exception as e:
        await cb.answer(f"❌ Ошибка при сохранении операции: {str(e)}")

# Обработчики для других кнопок из категорий
@router.callback_query(
    StateFilter(OperationStates.waiting_for_category),
    F.data == "add_category"
)
async def add_new_category_from_operation(cb: CallbackQuery, state: FSMContext):
    await cb.answer("⚠️ Функция добавления новой категории пока не реализована. Выберите существующую категорию.")

@router.callback_query(
    StateFilter(OperationStates.waiting_for_category),
    F.data == "main_menu"
)
async def cancel_operation(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text(
        "❌ Создание операции отменено.",
        reply_markup=main_menu_keyboard()
    )
    await cb.answer()