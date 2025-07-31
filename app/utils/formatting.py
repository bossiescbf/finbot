from html import escape
from typing import List
from app.database.models import Category


def two_cols(categories: List[Category], col_width: int = 25) -> str:
    """
    Форматирует список категорий в два столбца для Telegram.
    
    Args:
        categories: Список категорий
        col_width: Ширина левого столбца (по умолчанию 20)
    
    Returns:
        Строка с категориями в формате <pre>...</pre> для HTML
    
    Example:
        💳 Возврат              🎁 Подарок
        💼 Зарплата            💰 Подработка
    """
    if not categories:
        return ""
    
    lines = []
    # Идём по парам: 0-1, 2-3, 4-5 ...
    for i in range(0, len(categories), 2):
        left = f"{categories[i].icon} {categories[i].name}"
        right = (
            f"{categories[i+1].icon} {categories[i+1].name}"
            if i + 1 < len(categories) else ""
        )
        
        # Экранируем HTML символы для безопасности
        left = escape(left)
        right = escape(right)
        
        # Выравниваем левый столбец и добавляем правый
        lines.append(f"{left.ljust(col_width)}{right}")
    
    return "<code>" + "\n".join(lines) + "</code>"


def format_categories_text(income_categories: List[Category], expense_categories: List[Category]) -> str:
    """
    Форматирует полный текст со всеми категориями пользователя.
    
    Args:
        income_categories: Список категорий доходов
        expense_categories: Список категорий расходов
    
    Returns:
        Отформатированный текст для отправки в Telegram
    """
    text = "📊 <b>Ваши категории:</b>\n\n"
    
    if income_categories:
        text += "💰 <b>Доходы:</b>\n"
        text += two_cols(income_categories) + "\n\n"
    
    if expense_categories:
        text += "💸 <b>Расходы:</b>\n"
        text += two_cols(expense_categories)
    
    return text


def format_amount(amount: float, currency: str = "₽") -> str:
    """
    Форматирует сумму для отображения.
    
    Args:
        amount: Сумма
        currency: Валюта (по умолчанию рубли)
    
    Returns:
        Отформатированная строка с суммой
    
    Example:
        1234.56 -> "1 234,56 ₽"
    """
    return f"{amount:,.2f} {currency}".replace(",", " ").replace(".", ",")