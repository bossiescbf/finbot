from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, or_, desc, asc, insert, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import User, Operation, Category, Budget, user_categories
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
    async def create_user(db: AsyncSession, telegram_id: int, first_name: str, 
                         last_name: Optional[str] = None, username: Optional[str] = None) -> User:
        """Создать нового пользователя с базовыми категориями"""
        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            username=username
        )
        db.add(user)
        await db.flush()  # Получаем ID пользователя
    
        # Добавляем базовые категории
        await CategoryCRUD.ensure_user_has_default_categories(db, user.id)
    
        await db.commit()
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
        user = await UserCRUD.create_user(
            db, 
            telegram_id=telegram_id,
            first_name=kwargs.get('first_name', 'Пользователь'),
            last_name=kwargs.get('last_name'),
            username=kwargs.get('username')
        )
        
        return user, True


class CategoryCRUD:
    @staticmethod
    async def get_user_categories(db: AsyncSession, user_id: int, is_income: Optional[bool] = None) -> List[Category]:
        """Получить категории пользователя"""
        query = (
            select(Category)
            .join(user_categories, Category.id == user_categories.c.category_id)
            .where(user_categories.c.user_id == user_id)
            .where(Category.is_active == True)
        )
    
        if is_income is not None:
            query = query.where(Category.is_income == is_income)
        
        query = query.order_by(Category.name)
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_category_by_id(db: AsyncSession, category_id: int) -> Optional[Category]:
        """Получить категорию по ID"""
        result = await db.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_or_get_category(db: AsyncSession, name: str, icon: str, is_income: bool) -> Category:
        """Создать новую категорию или получить существующую по имени"""
        # Проверяем существование категории
        result = await db.execute(
            select(Category).where(Category.name == name)
        )
        category = result.scalar_one_or_none()
    
        if not category:
            category = Category(
                name=name,
                icon=icon,
                is_income=is_income,
                is_default=False,
                is_active=True
            )
            db.add(category)
            await db.flush()
        
        return category
    
    @staticmethod
    async def add_category_to_user(db: AsyncSession, user_id: int, category_id: int) -> bool:
        """Добавить категорию пользователю"""
        # Проверяем, есть ли уже такая связь
        result = await db.execute(
            select(user_categories)
            .where(
                and_(
                    user_categories.c.user_id == user_id,
                    user_categories.c.category_id == category_id
                )
            )
        )
    
        if result.scalar_one_or_none():
            return False  # Связь уже существует
    
        # Создаем связь
        stmt = insert(user_categories).values(
            user_id=user_id,
            category_id=category_id
        )
        await db.execute(stmt)
        return True
    
    @staticmethod
    async def remove_category_from_user(db: AsyncSession, user_id: int, category_id: int) -> bool:
        """Удалить категорию у пользователя"""
        stmt = delete(user_categories).where(
            and_(
                user_categories.c.user_id == user_id,
                user_categories.c.category_id == category_id
            )
        )
        result = await db.execute(stmt)
        return result.rowcount > 0
    
    @staticmethod
    async def ensure_user_has_default_categories(db: AsyncSession, user_id: int):
        """Убедиться, что у пользователя есть все базовые категории"""
        # Получаем базовые категории
        default_categories = await db.execute(
            select(Category).where(Category.is_default == True)
        )
        default_categories = default_categories.scalars().all()
        
        # Получаем категории пользователя
        user_category_ids = await db.execute(
            select(user_categories.c.category_id)
            .where(user_categories.c.user_id == user_id)
        )
        user_category_ids = {row[0] for row in user_category_ids.all()}
        
        # Добавляем недостающие базовые категории
        for category in default_categories:
            if category.id not in user_category_ids:
                await CategoryCRUD.add_category_to_user(db, user_id, category.id)


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
    async def get_operations_by_user(db: AsyncSession, user_id: int, limit: int = 100) -> List[Operation]:
        """Получить операции пользователя с категориями"""
        query = (
            select(Operation)
            .options(selectinload(Operation.category))
            .where(Operation.user_id == user_id)
            .order_by(Operation.created_at.desc())
            .limit(limit)
        )
        
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
        operations = await OperationCRUD.get_operations_by_user(
            db, user_id, limit=1000
        )
        
        # Фильтруем по периоду
        filtered_operations = [
            op for op in operations
            if start_date <= op.occurred_at <= end_date
        ]
        
        # Группировка по категориям
        categories_stats = {}
        total_income = Decimal('0')
        total_expense = Decimal('0')
        
        for op in filtered_operations:
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
            "operations_count": len(filtered_operations),
            "categories": categories_stats,
            "period": {
                "start": start_date,
                "end": end_date
            }
        }
    
    @staticmethod
    async def get_recent_operations(db: AsyncSession, user_id: int, limit: int = 10) -> List[Operation]:
        """Получить последние операции пользователя"""
        return await OperationCRUD.get_operations_by_user(db, user_id, limit=limit)


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
        end_date = budget.end_date or datetime.now(timezone.utc)
        
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