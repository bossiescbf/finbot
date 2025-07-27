from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional

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
        InlineKeyboardButton(text="📁 Категории", callback_data="categories"),
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

def categories_keyboard(categories: List[dict], operation_type: str = "expense") -> InlineKeyboardMarkup:
    """Клавиатура выбора категории"""
    keyboard = InlineKeyboardBuilder()
    
    # Добавляем категории по две в ряд
    for i in range(0, len(categories), 2):
        row_buttons = []
        for j in range(2):
            if i + j < len(categories):
                cat = categories[i + j]
                icon = cat.get('icon', '📝')
                name = cat['name']
                callback_data = f"cat_{cat['id']}"
                row_buttons.append(
                    InlineKeyboardButton(text=f"{icon} {name}", callback_data=callback_data)
                )
        keyboard.row(*row_buttons)
    
    # Кнопки управления
    keyboard.row(
        InlineKeyboardButton(text="➕ Новая категория", callback_data=f"new_category_{operation_type}")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_operation_type")
    )
    
    return keyboard.as_markup()

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

def categories_management_keyboard() -> InlineKeyboardMarkup:
    """Управление категориями"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.row(
        InlineKeyboardButton(text="➕ Добавить категорию", callback_data="add_category"),
        InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_categories")
    )
    keyboard.row(
        InlineKeyboardButton(text="📊 Категории доходов", callback_data="show_income_categories"),
        InlineKeyboardButton(text="💸 Категории расходов", callback_data="show_expense_categories")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_main")
    )
    
    return keyboard.as_markup()

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