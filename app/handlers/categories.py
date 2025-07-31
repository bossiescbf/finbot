from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud import CategoryCRUD
from app.keyboards.inline import (
    get_categories_keyboard, 
    get_back_keyboard,
    edit_categories_keyboard,
    edit_category_actions_keyboard,
    delete_category_confirmation_keyboard,
    category_type_selection_keyboard
)
from app.middlewares.auth import auth_required
from app.utils.formatting import format_categories_text

router = Router()

class AddCategoryStates(StatesGroup):
    waiting_name = State()
    waiting_icon = State()
    waiting_type = State()

@router.callback_query(F.data == "categories_menu")
@auth_required
async def show_categories_menu(call: CallbackQuery, user, db: AsyncSession, **kwargs):
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

    # Используем функцию из utils
    text = format_categories_text(income_categories, expense_categories)
    
    keyboard = get_categories_keyboard()
    await call.message.edit_text(
        text, 
        reply_markup=keyboard.as_markup(), 
        parse_mode="HTML"
    )

@router.callback_query(F.data == "edit_categories")
@auth_required
async def show_edit_categories_menu(call: CallbackQuery, user, db: AsyncSession):
    """Показать меню редактирования категорий"""
    # Получаем все категории пользователя
    income_categories = await CategoryCRUD.get_user_categories(db, user.id, is_income=True)
    expense_categories = await CategoryCRUD.get_user_categories(db, user.id, is_income=False)
    
    if not income_categories and not expense_categories:
        await call.message.edit_text(
            "❌ У вас пока нет категорий для редактирования.\n\n"
            "Сначала добавьте категории через кнопку ➕ Добавить категорию",
            reply_markup=get_back_keyboard().as_markup()
        )
        return
    
    # Используем функцию из inline.py
    keyboard = edit_categories_keyboard(income_categories, expense_categories)
    
    await call.message.edit_text(
        "✏️ **Редактирование категорий**\n\n"
        "Выберите категорию для редактирования:",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("edit_category:"))
@auth_required
async def edit_specific_category(call: CallbackQuery, user, db: AsyncSession):
    """Показать меню редактирования конкретной категории"""
    category_id = int(call.data.split(":")[1])
    
    # Получаем категорию из базы данных
    category = await CategoryCRUD.get_category_by_id(db, category_id)
    
    if not category:
        await call.answer("❌ Категория не найдена", show_alert=True)
        return
    
    # Проверяем, что категория принадлежит пользователю
    user_categories = await CategoryCRUD.get_user_categories(db, user.id)
    if category not in user_categories:
        await call.answer("❌ У вас нет доступа к этой категории", show_alert=True)
        return
    
    # Используем функцию из inline.py
    keyboard = edit_category_actions_keyboard(category_id)
    
    category_type = "доходов" if category.is_income else "расходов"
    
    await call.message.edit_text(
        f"✏️ **Редактирование категории**\n\n"
        f"**Категория:** {category.icon} {category.name}\n"
        f"**Тип:** {category_type}\n\n"
        f"Выберите действие:",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("delete_category:"))  
@auth_required
async def confirm_delete_category(call: CallbackQuery, user, db: AsyncSession):
    """Подтверждение удаления категории"""
    category_id = int(call.data.split(":")[1])
    
    # Получаем категорию
    category = await CategoryCRUD.get_category_by_id(db, category_id)
    
    if not category:
        await call.answer("❌ Категория не найдена", show_alert=True)
        return
    
    # Используем функцию из inline.py
    keyboard = delete_category_confirmation_keyboard(category_id)
    
    await call.message.edit_text(
        f"⚠️ **Подтверждение удаления**\n\n"
        f"Вы уверены, что хотите удалить категорию:\n"
        f"**{category.icon} {category.name}**?\n\n"
        f"❗️ Это действие нельзя отменить!",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("confirm_delete:"))
@auth_required  
async def delete_category_confirmed(call: CallbackQuery, user, db: AsyncSession):
    """Окончательное удаление категории"""
    category_id = int(call.data.split(":")[1])
    
    try:
        # Удаляем категорию у пользователя
        success = await CategoryCRUD.remove_category_from_user(db, user.id, category_id)
        await db.commit()
        
        if success:
            await call.message.edit_text(
                "✅ **Категория успешно удалена!**\n\n"
                "Категория больше не отображается в ваших списках.",
                reply_markup=get_back_keyboard().as_markup(),
                parse_mode="Markdown"
            )
        else:
            await call.message.edit_text(
                "❌ **Ошибка при удалении категории**\n\n"
                "Возможно, категория уже была удалена ранее.",
                reply_markup=get_back_keyboard().as_markup(),
                parse_mode="Markdown"
            )
            
    except Exception as e:
        await call.message.edit_text(
            f"❌ **Произошла ошибка:** {str(e)}",
            reply_markup=get_back_keyboard().as_markup(),
            parse_mode="Markdown"
        )

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
    
    # Используем функцию из inline.py
    keyboard = category_type_selection_keyboard()
    
    await message.reply(
        "💰 Выберите тип категории:",
        reply_markup=keyboard.as_markup()
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