from aiogram.fsm.state import State, StatesGroup

class AddOperationStates(StatesGroup):
    """Состояния для добавления доходов/расходов"""
    waiting_for_amount = State()
    waiting_for_description = State()
    waiting_for_category = State()
    waiting_for_confirmation = State()

class QuickAddStates(StatesGroup):
    """Состояния для быстрого добавления операций"""
    waiting_for_operation = State()  # Ожидаем "1200 обед" или "+5000 зарплата"

class CategoryStates(StatesGroup):
    """Состояния для управления категориями"""
    waiting_for_category_name = State()
    waiting_for_category_icon = State()
    waiting_for_category_type = State()
    selecting_category_to_edit = State()
    waiting_for_new_category_name = State()

class ReportStates(StatesGroup):
    """Состояния для генерации отчетов"""
    selecting_report_type = State()
    selecting_period = State()
    waiting_for_custom_dates = State()

class SettingsStates(StatesGroup):
    """Состояния для настроек пользователя"""
    selecting_setting = State()
    waiting_for_currency = State()
    waiting_for_timezone = State()
    waiting_for_daily_limit = State()
    waiting_for_monthly_limit = State()

class BudgetStates(StatesGroup):
    """Состояния для управления бюджетами"""
    selecting_category_for_budget = State()
    waiting_for_budget_amount = State()
    waiting_for_budget_period = State()

class EditOperationStates(StatesGroup):
    """Состояния для редактирования операций"""
    selecting_operation = State()
    selecting_field_to_edit = State()
    waiting_for_new_amount = State()
    waiting_for_new_description = State()
    waiting_for_new_category = State()

# Дополнительные состояния для сложных сценариев
class ImportStates(StatesGroup):
    """Состояния для импорта данных"""
    waiting_for_file = State()
    confirming_import = State()

class ExportStates(StatesGroup):
    """Состояния для экспорта данных"""
    selecting_format = State()
    selecting_period_for_export = State()
    confirming_export = State()