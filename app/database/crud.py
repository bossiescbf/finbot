from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import User, Operation, Category, Budget
from ..schemas.user import UserCreate, UserUpdate
from ..schemas.operation import OperationCreate, OperationUpdate

class UserCRUD:
    @staticmethod
    async def get_by_telegram_id(db: AsyncSession, telegram_id: int) -> Optional[User]:
        """Получить пользователя по telegram_id"""
        result = await db.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(db: AsyncSession, user_data: UserCreate) -> User:
        """Создать нового пользователя"""
        user = User(**user_data.dict())
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def update(db: AsyncSession, user: User, user_data: UserUpdate) -> User:
        """Обновить данные пользователя"""
        for field, value in user_data.dict(exclude_unset=True).items():
            setattr(user, field, value)
        
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def get_or_create_user(db: AsyncSession, telegram_id: int, **kwargs) -> tuple[User, bool]:
        """Получить существующего пользователя или создать нового"""
        user = await UserCRUD.get_by_telegram_id(db, telegram_id)
        
        if user:
            return user, False
        
        # Создаем нового пользователя
        user_data = UserCreate(telegram_id=telegram_id, **kwargs)
        user = await UserCRUD.create(db, user_data)
        
        # Создаем категории по умолчанию
        await CategoryCRUD.create_default_categories(db, user.id)
        
        return user, True

class CategoryCRUD:
    @staticmethod
    async def get_user_categories(db: AsyncSession, user_id: int, is_income: Optional[bool] = None) -> List[Category]:
        """Получить категории пользователя"""
        query = select(Category).where(
            and_(Category.user_id == user_id, Category.is_active == True)
        )
        
        if is_income is not None:
            query = query.where(Category.is_income == is_income)
        
        result = await db.execute(query.order_by(Category.name))
        return result.scalars().all()
    
    @staticmethod
    async def create(db: AsyncSession, category_data: dict) -> Category:
        """Создать новую категорию"""
        category = Category(**category_data)
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category
    
    @staticmethod
    async def get_by_id(db: AsyncSession, category_id: int, user_id: int) -> Optional[Category]:
        """Получить категорию по ID для конкретного пользователя"""
        result = await db.execute(
            select(Category).where(
                and_(Category.id == category_id, Category.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_default_categories(db: AsyncSession, user_id: int):
        """Создать категории по умолчанию для нового пользователя"""
        
        # Категории расходов
        expense_categories = [
            {"name": "🍕 Еда", "icon": "🍕", "is_income": False, "is_default": True},
            {"name": "🚗 Транспорт", "icon": "🚗", "is_income": False, "is_default": True},
            {"name": "🏠 Жилье", "icon": "🏠", "is_income": False, "is_default": True},
            {"name": "👕 Одежда", "icon": "👕", "is_income": False, "is_default": True},
            {"name": "🎬 Развлечения", "icon": "🎬", "is_income": False, "is_default": True},
            {"name": "💊 Здоровье", "icon": "💊", "is_income": False, "is_default": True},
            {"name": "📚 Образование", "icon": "📚", "is_income": False, "is_default": True},
            {"name": "🎁 Подарки", "icon": "🎁", "is_income": False, "is_default": True},
            {"name": "📱 Связь", "icon": "📱", "is_income": False, "is_default": True},
            {"name": "🛒 Покупки", "icon": "🛒", "is_income": False, "is_default": True},
        ]
        
        # Категории доходов
        income_categories = [
            {"name": "💼 Зарплата", "icon": "💼", "is_income": True, "is_default": True},
            {"name": "💰 Подработка", "icon": "💰", "is_income": True, "is_default": True},
            {"name": "🎁 Подарок", "icon": "🎁", "is_income": True, "is_default": True},
            {"name": "📈 Инвестиции", "icon": "📈", "is_income": True, "is_default": True},
            {"name": "💳 Возврат", "icon": "💳", "is_income": True, "is_default": True},
        ]
        
        all_categories = expense_categories + income_categories
        
        for cat_data in all_categories:
            cat_data["user_id"] = user_id
            await CategoryCRUD.create(db, cat_data)

class OperationCRUD:
    @staticmethod
    async def create(db: AsyncSession, operation_data: OperationCreate, user_id: int) -> Operation:
        """Создать новую операцию"""
        operation = Operation(**operation_data.dict(), user_id=user_id)
        db.add(operation)
        await db.commit()
        await db.refresh(operation)
        return operation
    
    @staticmethod
    async def get_user_operations(
        db: AsyncSession, 
        user_id: int, 
        limit: int = 50,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category_id: Optional[int] = None,
        operation_type: Optional[str] = None
    ) -> List[Operation]:
        """Получить операции пользователя с фильтрами"""
        
        query = select(Operation).options(
            selectinload(Operation.category)
        ).where(Operation.user_id == user_id)
        
        # Фильтры
        if start_date:
            query = query.where(Operation.occurred_at >= start_date)
        if end_date:
            query = query.where(Operation.occurred_at <= end_date)
        if category_id:
            query = query.where(Operation.category_id == category_id)
        if operation_type:
            query = query.where(Operation.type == operation_type)
        
        # Сортировка и пагинация
        query = query.order_by(desc(Operation.occurred_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_by_id(db: AsyncSession, operation_id: int, user_id: int) -> Optional[Operation]:
        """Получить операцию по ID для конкретного пользователя"""
        result = await db.execute(
            select(Operation).options(selectinload(Operation.category)).where(
                and_(Operation.id == operation_id, Operation.user_id == user_id)
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update(db: AsyncSession, operation: Operation, operation_data: OperationUpdate) -> Operation:
        """Обновить операцию"""
        for field, value in operation_data.dict(exclude_unset=True).items():
            setattr(operation, field, value)
        
        await db.commit()
        await db.refresh(operation)
        return operation
    
    @staticmethod
    async def delete(db: AsyncSession, operation: Operation):
        """Удалить операцию"""
        await db.delete(operation)
        await db.commit()
    
    @staticmethod
    async def get_balance(db: AsyncSession, user_id: int) -> Dict[str, Decimal]:
        """Получить баланс пользователя"""
        # Получаем сумму доходов
        income_result = await db.execute(
            select(func.coalesce(func.sum(Operation.amount), 0)).where(
                and_(Operation.user_id == user_id, Operation.type == 'income')
            )
        )
        total_income = income_result.scalar()
        
        # Получаем сумму расходов
        expense_result = await db.execute(
            select(func.coalesce(func.sum(Operation.amount), 0)).where(
                and_(Operation.user_id == user_id, Operation.type == 'expense')
            )
        )
        total_expense = expense_result.scalar()
        
        balance = total_income - total_expense
        
        return {
            "balance": balance,
            "total_income": total_income,
            "total_expense": total_expense
        }
    
    @staticmethod
    async def get_statistics_by_period(
        db: AsyncSession, 
        user_id: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Получить статистику за период"""
        
        # Операции за период
        operations = await OperationCRUD.get_user_operations(
            db, user_id, start_date=start_date, end_date=end_date, limit=1000
        )
        
        # Группировка по категориям
        categories_stats = {}
        total_income = Decimal('0')
        total_expense = Decimal('0')
        
        for op in operations:
            category_name = op.category.name if op.category else "Без категории"
            
            if category_name not in categories_stats:
                categories_stats[category_name] = {
                    "income": Decimal('0'),
                    "expense": Decimal('0'),
                    "count": 0
                }
            
            if op.type == 'income':
                categories_stats[category_name]["income"] += op.amount
                total_income += op.amount
            else:
                categories_stats[category_name]["expense"] += op.amount
                total_expense += op.amount
            
            categories_stats[category_name]["count"] += 1
        
        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
            "operations_count": len(operations),
            "categories": categories_stats,
            "period": {
                "start": start_date,
                "end": end_date
            }
        }
    
    @staticmethod
    async def get_recent_operations(db: AsyncSession, user_id: int, limit: int = 10) -> List[Operation]:
        """Получить последние операции пользователя"""
        return await OperationCRUD.get_user_operations(db, user_id, limit=limit)

class BudgetCRUD:
    @staticmethod
    async def create(db: AsyncSession, budget_data: dict) -> Budget:
        """Создать новый бюджет"""
        budget = Budget(**budget_data)
        db.add(budget)
        await db.commit()
        await db.refresh(budget)
        return budget
    
    @staticmethod
    async def get_user_budgets(db: AsyncSession, user_id: int) -> List[Budget]:
        """Получить активные бюджеты пользователя"""
        result = await db.execute(
            select(Budget).options(selectinload(Budget.category)).where(
                and_(Budget.user_id == user_id, Budget.is_active == True)
            )
        )
        return result.scalars().all()
    
    @staticmethod
    async def check_budget_exceeded(db: AsyncSession, user_id: int, category_id: int, amount: Decimal) -> Optional[Dict]:
        """Проверить превышение бюджета"""
        # Получаем активные бюджеты для категории
        result = await db.execute(
            select(Budget).where(
                and_(
                    Budget.user_id == user_id,
                    Budget.category_id == category_id,
                    Budget.is_active == True
                )
            )
        )
        budget = result.scalar_one_or_none()
        
        if not budget:
            return None
        
        # Вычисляем потраченную сумму за период бюджета
        start_date = budget.start_date
        end_date = budget.end_date or datetime.now()
        
        spent_result = await db.execute(
            select(func.coalesce(func.sum(Operation.amount), 0)).where(
                and_(
                    Operation.user_id == user_id,
                    Operation.category_id == category_id,
                    Operation.type == 'expense',
                    Operation.occurred_at >= start_date,
                    Operation.occurred_at <= end_date
                )
            )
        )
        spent_amount = spent_result.scalar()
        
        new_total = spent_amount + amount
        
        if new_total > budget.limit_amount:
            return {
                "budget_exceeded": True,
                "budget_limit": budget.limit_amount,
                "spent_amount": spent_amount,
                "new_total": new_total,
                "excess_amount": new_total - budget.limit_amount
            }
        
        return {
            "budget_exceeded": False,
            "budget_limit": budget.limit_amount,
            "spent_amount": spent_amount,
            "new_total": new_total,
            "remaining": budget.limit_amount - new_total
        }