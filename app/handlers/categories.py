from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud import CategoryCRUD
from app.keyboards.inline import get_categories_keyboard, get_back_keyboard
from app.middlewares.auth import auth_required

router = Router()

class AddCategoryStates(StatesGroup):
    waiting_name = State()
    waiting_icon = State()
    waiting_type = State()

@router.callback_query(F.data == "categories_menu")
@auth_required
async def show_categories_menu(call: CallbackQuery, user, db: AsyncSession):
    """Показать меню категорий"""
    income_categories = await CategoryCRUD.get_user_categories(db, user.id, is_income=True)
    expense_categories = await CategoryCRUD.get_user_categories(db, user.id, is_income=False)
    
    if not income_categories and not expense_categories:
        text = "📁 Категории не найдены\n\n"
        text += "Нажмите кнопку ниже, чтобы добавить категорию"
        keyboard = get_back_keyboard()
        keyboard.button(text="➕ Добавить категорию", callback_data="add_category")
        await call.message.edit_text(text, reply_markup=keyboard.as_markup())
        return
    
    text = "📊 **Ваши категории:**\n\n"
    
    if income_categories:
        text += "💰 **Доходы:**\n"
        for cat in income_categories:
            text += f"{cat.icon} {cat.name}\n"
        text += "\n"
    
    if expense_categories:
        text += "💸 **Расходы:**\n"
        for cat in expense_categories:
            text += f"{cat.icon} {cat.name}\n"
    
    keyboard = get_categories_keyboard()
    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data == "add_category")
@auth_required
async def start_add_category(call: CallbackQuery, user, state: FSMContext):
    """Начать процесс добавления категории"""
    await call.message.edit_text(
        "📝 Введите название новой категории:",
        reply_markup=get_back_keyboard().as_markup()
    )
    await state.set_state(AddCategoryStates.waiting_name)

@router.message(AddCategoryStates.waiting_name)
@auth_required
async def process_category_name(message: Message, user, state: FSMContext, db: AsyncSession):
    """Обработать название категории"""
    category_name = message.text.strip()
    
    if len(category_name) > 100:
        await message.reply("❌ Название категории слишком длинное (максимум 100 символов)")
        return
    
    await state.update_data(name=category_name)
    await message.reply(
        f"📝 Название: {category_name}\n\n"
        "🎨 Теперь отправьте эмоджи-иконку для категории:",
        reply_markup=get_back_keyboard().as_markup()
    )
    await state.set_state(AddCategoryStates.waiting_icon)

@router.message(AddCategoryStates.waiting_icon)
@auth_required
async def process_category_icon(message: Message, user, state: FSMContext):
    """Обработать иконку категории"""
    icon = message.text.strip()
    
    if len(icon) > 10:
        await message.reply("❌ Иконка слишком длинная (максимум 10 символов)")
        return
    
    await state.update_data(icon=icon)
    
    # Клавиатура выбора типа категории
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Доход", callback_data="category_type:income")
    kb.button(text="💸 Расход", callback_data="category_type:expense")
    kb.button(text="🔙 Назад", callback_data="categories_menu")
    kb.adjust(2, 1)
    
    await message.reply(
        "💰 Выберите тип категории:",
        reply_markup=kb.as_markup()
    )
    await state.set_state(AddCategoryStates.waiting_type)

@router.callback_query(F.data.startswith("category_type:"))
@auth_required
async def process_category_type(call: CallbackQuery, user, state: FSMContext, db: AsyncSession):
    """Обработать тип категории и создать её"""
    category_type = call.data.split(":")[1]
    is_income = category_type == "income"
    
    data = await state.get_data()
    name = data.get("name")
    icon = data.get("icon")
    
    try:
        # Создаём или получаем категорию
        category = await CategoryCRUD.create_or_get_category(db, name, icon, is_income)
        
        # Добавляем категорию пользователю
        success = await CategoryCRUD.add_category_to_user(db, user.id, category.id)
        await db.commit()
        
        if success:
            type_text = "доходов" if is_income else "расходов"
            await call.message.edit_text(
                f"✅ Категория **{icon} {name}** ({type_text}) успешно добавлена!",
                parse_mode="Markdown"
            )
        else:
            await call.message.edit_text(
                f"ℹ️ Категория **{icon} {name}** уже есть в вашем списке",
                parse_mode="Markdown"
            )
            
    except Exception as e:
        await call.message.edit_text(f"❌ Ошибка при создании категории: {str(e)}")
    
    await state.clear()

@router.callback_query(F.data == "categories_income")
@auth_required
async def show_income_categories(call: CallbackQuery, user, db: AsyncSession):
    """Показать категории доходов"""
    categories = await CategoryCRUD.get_user_categories(db, user.id, is_income=True)
    
    if not categories:
        await call.message.edit_text(
            "💰 У вас пока нет категорий доходов",
            reply_markup=get_back_keyboard().as_markup()
        )
        return
    
    text = "💰 **Категории доходов:**\n\n"
    for cat in categories:
        text += f"{cat.icon} {cat.name}\n"
    
    await call.message.edit_text(
        text,
        reply_markup=get_back_keyboard().as_markup(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "categories_expenses")
@auth_required
async def show_expense_categories(call: CallbackQuery, user, db: AsyncSession):
    """Показать категории расходов"""
    categories = await CategoryCRUD.get_user_categories(db, user.id, is_income=False)
    
    if not categories:
        await call.message.edit_text(
            "💸 У вас пока нет категорий расходов",
            reply_markup=get_back_keyboard().as_markup()
        )
        return
    
    text = "💸 **Категории расходов:**\n\n"
    for cat in categories:
        text += f"{cat.icon} {cat.name}\n"
    
    await call.message.edit_text(
        text,
        reply_markup=get_back_keyboard().as_markup(),
        parse_mode="Markdown"
    )