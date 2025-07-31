from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional
from app.database.models import Category

def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню бота"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="💰 Добавить доход", callback_data="add_income"),
        InlineKeyboardButton(text="💸 Добавить расход", callback_data="add_expense")
    )
    keyboard.row(
        InlineKeyboardButton(text="📊 Отчеты", callback_data="reports"),
        InlineKeyboardButton(text="📈 Баланс", callback_data="balance")
    )
    keyboard.row(
        InlineKeyboardButton(text="📁 Категории", callback_data="categories_menu"),
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")
    )
    keyboard.row(
        InlineKeyboardButton(text="❓ Помощь", callback_data="help")
    )
    
    return keyboard.as_markup()

def operations_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Добавить доход", callback_data="add_income")],
        [InlineKeyboardButton("Добавить расход", callback_data="add_expense")],
    ])

def get_categories_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура меню категорий в 2 столбца"""
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Добавить категорию", callback_data="add_category")
    kb.button(text="✏️ Редактировать", callback_data="edit_categories")
    kb.button(text="🔙 Назад", callback_data="back_to_main")
    
    kb.adjust(2, 1)
    
    return kb

def confirm_operation_keyboard() -> InlineKeyboardMarkup:
    """Подтверждение операции"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="✅ Сохранить", callback_data="confirm_save"),
        InlineKeyboardButton(text="✏️ Изменить", callback_data="confirm_edit")
    )
    keyboard.row(
        InlineKeyboardButton(text="❌ Отменить", callback_data="confirm_cancel")
    )
    
    return keyboard.as_markup()

def reports_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню отчетов"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="📅 За сегодня", callback_data="report_today"),
        InlineKeyboardButton(text="📆 За неделю", callback_data="report_week")
    )
    keyboard.row(
        InlineKeyboardButton(text="🗓️ За месяц", callback_data="report_month"),
        InlineKeyboardButton(text="🗓️ За год", callback_data="report_year")
    )
    keyboard.row(
        InlineKeyboardButton(text="📋 Произвольный период", callback_data="report_custom")
    )
    keyboard.row(
        InlineKeyboardButton(text="📊 По категориям", callback_data="report_categories"),
        InlineKeyboardButton(text="📈 Тренды", callback_data="report_trends")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main")
    )
    
    return keyboard.as_markup()

def settings_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню настроек"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="💱 Валюта", callback_data="setting_currency"),
        InlineKeyboardButton(text="🌍 Часовой пояс", callback_data="setting_timezone")
    )
    keyboard.row(
        InlineKeyboardButton(text="📊 Дневной лимит", callback_data="setting_daily_limit"),
        InlineKeyboardButton(text="📈 Месячный лимит", callback_data="setting_monthly_limit")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔔 Уведомления", callback_data="setting_notifications"),
        InlineKeyboardButton(text="🎨 Тема", callback_data="setting_theme")
    )
    keyboard.row(
        InlineKeyboardButton(text="📤 Экспорт данных", callback_data="export_data"),
        InlineKeyboardButton(text="📥 Импорт данных", callback_data="import_data")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main")
    )
    
    return keyboard.as_markup()

def get_category_selection_keyboard(categories: List[Category], operation_type: str = "", columns: int = 3) -> InlineKeyboardBuilder:
    """Клавиатура выбора категории для операции"""
    kb = InlineKeyboardBuilder()
    
    for category in categories:
        callback_data = f"select_category:{category.id}"
        if operation_type:
            callback_data += f":{operation_type}"
        
        kb.button(
            text=f"{category.icon} {category.name}",
            callback_data=callback_data
        )
    
    # Добавляем служебные кнопки
    kb.button(text="➕ Новая категория", callback_data="add_category")
    kb.button(text="🔙 Назад", callback_data="main_menu")
    
    # Размещаем категории в указанное количество столбцов
    categories_count = len(categories)
    if categories_count > 0:
        kb.adjust(*([columns] * (categories_count // columns) + 
                   ([categories_count % columns] if categories_count % columns else []) +
                   [1, 1]))  # Служебные кнопки по одной в строке
    else:
        kb.adjust(1, 1)  # Только служебные кнопки
    
    return kb

def get_back_keyboard() -> InlineKeyboardBuilder:
    """Простая клавиатура с кнопкой Назад"""
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Назад", callback_data="categories_menu")
    return kb

def currency_keyboard() -> InlineKeyboardMarkup:
    """Выбор валюты"""
    currencies = [
        ("🇷🇺 Рубль", "RUB"),
        ("🇺🇸 Доллар", "USD"),
        ("🇪🇺 Евро", "EUR"),
        ("🇬🇧 Фунт", "GBP"),
        ("🇨🇳 Юань", "CNY"),
        ("🇯🇵 Иена", "JPY")
    ]
    
    keyboard = InlineKeyboardBuilder()
    
    for name, code in currencies:
        keyboard.row(
            InlineKeyboardButton(text=name, callback_data=f"currency_{code}")
        )
    
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_settings")
    )
    
    return keyboard.as_markup()

def yes_no_keyboard(yes_callback: str, no_callback: str) -> InlineKeyboardMarkup:
    """Универсальная клавиатура Да/Нет"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="✅ Да", callback_data=yes_callback),
        InlineKeyboardButton(text="❌ Нет", callback_data=no_callback)
    )
    
    return keyboard.as_markup()

def pagination_keyboard(current_page: int, total_pages: int, callback_prefix: str) -> InlineKeyboardMarkup:
    """Клавиатура пагинации"""
    keyboard = InlineKeyboardBuilder()
    
    buttons = []
    
    # Кнопка "Назад"
    if current_page > 1:
        buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"{callback_prefix}_page_{current_page - 1}")
        )
    
    # Текущая страница
    buttons.append(
        InlineKeyboardButton(text=f"{current_page}/{total_pages}", callback_data="current_page")
    )
    
    # Кнопка "Вперед"
    if current_page < total_pages:
        buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=f"{callback_prefix}_page_{current_page + 1}")
        )
    
    keyboard.row(*buttons)
    
    return keyboard.as_markup()

def quick_amounts_keyboard(operation_type: str) -> InlineKeyboardMarkup:
    """Быстрые суммы для операций"""
    keyboard = InlineKeyboardBuilder()
    
    if operation_type == "expense":
        amounts = [100, 200, 500, 1000, 2000, 5000]
    else:  # income
        amounts = [1000, 5000, 10000, 25000, 50000, 100000]
    
    # По 3 кнопки в ряд
    for i in range(0, len(amounts), 3):
        row_buttons = []
        for j in range(3):
            if i + j < len(amounts):
                amount = amounts[i + j]
                row_buttons.append(
                    InlineKeyboardButton(
                        text=f"{amount:,} ₽".replace(',', ' '), 
                        callback_data=f"quick_amount_{amount}"
                    )
                )
        keyboard.row(*row_buttons)
    
    keyboard.row(
        InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="manual_amount")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
    )
    
    return keyboard.as_markup()
    
def edit_categories_keyboard(income_categories: List[Category], expense_categories: List[Category]) -> InlineKeyboardBuilder:
    """Клавиатура редактирования категорий с выбором конкретной категории"""
    kb = InlineKeyboardBuilder()
    
    # Добавляем категории доходов
    for cat in income_categories:
        kb.button(
            text=f"💰 {cat.icon} {cat.name}",
            callback_data=f"edit_category:{cat.id}"
        )
    
    # Добавляем категории расходов  
    for cat in expense_categories:
        kb.button(
            text=f"💸 {cat.icon} {cat.name}",
            callback_data=f"edit_category:{cat.id}"
        )
    
    # Кнопка "Назад"
    kb.button(text="🔙 Назад", callback_data="categories_menu")
    
    # Размещаем по 2 категории в ряд, кнопку "Назад" отдельно
    categories_count = len(income_categories) + len(expense_categories)
    if categories_count > 0:
        kb.adjust(*([2] * (categories_count // 2) + 
                    ([1] if categories_count % 2 else []) + 
                    [1]))  # Кнопка "Назад" отдельно
    else:
        kb.adjust(1)  # Только кнопка "Назад"
    
    return kb

def edit_category_actions_keyboard(category_id: int) -> InlineKeyboardBuilder:
    """Клавиатура действий с конкретной категорией"""
    kb = InlineKeyboardBuilder()
    kb.button(text="🗑️ Удалить категорию", callback_data=f"delete_category:{category_id}")
    kb.button(text="🔙 Назад к списку", callback_data="edit_categories")
    kb.adjust(1, 1)
    return kb

def delete_category_confirmation_keyboard(category_id: int) -> InlineKeyboardBuilder:
    """Клавиатура подтверждения удаления категории"""
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да, удалить", callback_data=f"confirm_delete:{category_id}")
    kb.button(text="❌ Отменить", callback_data=f"edit_category:{category_id}")
    kb.adjust(1, 1)
    return kb

def category_type_selection_keyboard() -> InlineKeyboardBuilder:
    """Клавиатура выбора типа категории"""
    kb = InlineKeyboardBuilder()
    kb.button(text="💰 Доход", callback_data="category_type:income")
    kb.button(text="💸 Расход", callback_data="category_type:expense")
    kb.button(text="🔙 Назад", callback_data="categories_menu")
    kb.adjust(2, 1)
    return kb
    
def balance_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для экрана баланса:
    🔙 Назад — возврат в главное меню
    🕑 История — показать последние 10 операций
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🕑 История", callback_data="history"),
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
        ]
    ])