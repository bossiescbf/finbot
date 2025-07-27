from aiogram import Router, types, F
from aiogram.filters import Command
from app.keyboards.inline import main_menu_keyboard

router = Router()

@router.message(Command("help"))
async def help_command(message: types.Message) -> None:
    """Обработчик команды /help"""
    help_text = """
📚 <b>Справка по командам FinBot</b>

<b>🔧 Основные команды:</b>
/start – Главное меню  
/help – Эта справка  
/balance – Показать баланс  
/add – Добавить операцию  
/report – Отчёты за период  
/categories – Управление категориями  
/settings – Настройки  
/cancel – Отменить текущее действие  

<b>⚡ Быстрое добавление:</b>
• <code>1200 обед</code> – расход 1200 ₽ в категории «обед»  
• <code>+50000 зарплата</code> – доход 50000 ₽ в категории «зарплата»  
• <code>500</code> – расход 500 ₽ (категория будет предложена)  

<b>📊 Отчёты:</b>
• За сегодня / неделю / месяц  
• По категориям  
• Произвольный период  
• Экспорт в Excel / PDF  

<b>🎯 Полезные функции:</b>
• Автоматические категории  
• Лимиты и бюджеты  
• Уведомления о превышениях  
• Статистика и тренды  
• Резервное копирование данных  

<b>💡 Совет:</b> для быстрой навигации используй кнопки меню или набери команды.

Нужна помощь? Напиши разработчику: @bossies
    """

    await message.answer(
        help_text.strip(),
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )


@router.callback_query(F.data == "help")
async def help_callback(callback: types.CallbackQuery) -> None:
    """Обработчик нажатия кнопки «Помощь» в главном меню"""
    await help_command(callback.message)
    await callback.answer()